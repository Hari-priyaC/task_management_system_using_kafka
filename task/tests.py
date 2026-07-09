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
        self.assertNotIn('connection_timeout_ms', kwargs)


class DLQRecoveryTests(TestCase):
    def test_reprocess_pending_dlq_entries_marks_resolved(self):
        entry = DLQLog.objects.create(
            original_topic='task-created',
            original_message={'task_id': 1},
            error='Kafka down',
            status='pending',
        )

        producer = KafkaProducerWithDLQ()
        with patch.object(producer, 'send_with_retry', return_value=True) as mock_send:
            processed = producer.reprocess_pending_dlq_entries()

        self.assertEqual(processed, 1)
        entry.refresh_from_db()
        self.assertEqual(entry.status, 'resolved')
        mock_send.assert_called_once_with(
            topic='task-created',
            message={'task_id': 1},
            dlq_topic='task-dlq',
        )
