from unittest.mock import patch

from django.test import SimpleTestCase, TestCase, override_settings

from analytics.models import DLQLog
from task.producer import KafkaProducerWithDLQ, get_topic_name


class KafkaProducerTests(SimpleTestCase):
    @override_settings(KAFKA_TOPICS={'task_created': 'custom-created'})
    def test_get_topic_name_uses_settings_dictionary(self):
        self.assertEqual(get_topic_name('task_created', 'fallback-topic'), 'custom-created')

    @patch('task.producer.KafkaProducer')
    def test_producer_uses_supported_timeout_config(self, mock_producer):
        KafkaProducerWithDLQ()

        kwargs = mock_producer.call_args.kwargs
        self.assertIn('request_timeout_ms', kwargs)
        self.assertIn('max_block_ms', kwargs)
        self.assertNotIn('connection_timeout_ms', kwargs)

    def test_send_with_retry_is_non_blocking(self):
        """The request-path entry point must return immediately regardless of
        how long the underlying publish-with-retry takes in the background."""
        import time

        producer = KafkaProducerWithDLQ()
        release = None

        def slow_publish(*args, **kwargs):
            time.sleep(0.3)
            return True

        with patch.object(producer, '_send_with_retry_sync', side_effect=slow_publish):
            start = time.time()
            accepted = producer.send_with_retry('task-created', {'task_id': 1})
            elapsed = time.time() - start

        self.assertTrue(accepted)
        self.assertLess(elapsed, 0.1)


class DLQRecoveryTests(TestCase):
    def test_reprocess_pending_dlq_entries_delegates_with_dlq_entry_id(self):
        """
        Status transitions for a reprocessed row happen inside
        _send_with_retry_sync (see test_send_with_retry_sync_* below) - this
        test only checks reprocess_pending_dlq_entries claims the row and
        passes dlq_entry_id through, so failures update it in place instead
        of minting a new DLQLog row (the original bug: one failed publish
        could balloon into a dozen duplicate DLQ rows).
        """
        entry = DLQLog.objects.create(
            original_topic='task-created',
            original_message={'task_id': 1},
            error='Kafka down',
            status='pending',
        )

        producer = KafkaProducerWithDLQ()
        with patch.object(producer, 'send_with_retry_sync', return_value=True) as mock_send:
            processed = producer.reprocess_pending_dlq_entries()

        self.assertEqual(processed, 1)
        mock_send.assert_called_once_with(
            topic='task-created',
            message={'task_id': 1},
            task_id=None,
            dlq_entry_id=entry.id,
        )

    def test_send_with_retry_sync_marks_dlq_resolved_on_success(self):
        entry = DLQLog.objects.create(
            original_topic='task-created',
            original_message={'task_id': 1},
            error='Kafka down',
            status='processing',
        )

        producer = KafkaProducerWithDLQ()
        mock_future = type('F', (), {'get': lambda self, timeout=None: None})()
        with patch.object(producer, '_ensure_producer', return_value=True), \
             patch.object(producer, 'producer') as mock_kafka_producer:
            mock_kafka_producer.send.return_value = mock_future
            success = producer.send_with_retry_sync(
                topic='task-created', message={'task_id': 1}, dlq_entry_id=entry.id,
            )

        self.assertTrue(success)
        entry.refresh_from_db()
        self.assertEqual(entry.status, 'resolved')
        self.assertIsNotNone(entry.resolved_at)

    def test_failed_retry_updates_existing_row_instead_of_creating_a_new_one(self):
        """Regression test for the duplicate-DLQ-row bug: a failed retry of an
        already-DLQ'd event must update that row, never insert a second one."""
        entry = DLQLog.objects.create(
            original_topic='task-created',
            original_message={'task_id': 1},
            error='Kafka down',
            retry_count=0,
            max_retries=3,
            status='processing',
        )

        producer = KafkaProducerWithDLQ()
        with patch.object(producer, '_ensure_producer', return_value=False):
            success = producer.send_with_retry_sync(
                topic='task-created', message={'task_id': 1}, dlq_entry_id=entry.id,
            )

        self.assertFalse(success)
        self.assertEqual(DLQLog.objects.count(), 1)
        entry.refresh_from_db()
        self.assertEqual(entry.retry_count, 1)
        self.assertEqual(entry.status, 'pending')
