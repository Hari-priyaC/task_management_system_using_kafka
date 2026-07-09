from kafka import KafkaProducer
import json
import uuid
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Publishing to Kafka happens here, off the request thread, so a slow/unreachable
# broker never adds latency to the HTTP response.
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix='kafka-publish')


def get_topic_name(topic_key, default_name='task-dlq'):
    """Resolve topic names from either a dict or an object-backed settings value."""
    topics = getattr(settings, 'KAFKA_TOPICS', {})
    if isinstance(topics, dict):
        return topics.get(topic_key, default_name)
    return getattr(topics, topic_key, default_name)


class KafkaProducerWithDLQ:
    """
    Publishes to Kafka with bounded retries and falls back to a DLQ table on
    failure. `send_with_retry` is fire-and-forget (non-blocking) for callers on
    the request path; `send_with_retry_sync` is the blocking version used by the
    DLQ recovery worker, which needs to know the outcome before updating status.
    """

    def __init__(self):
        self.bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS
        self.max_retries = getattr(settings, 'MAX_RETRY_ATTEMPTS', 3)
        retry_backoff_ms = getattr(settings, 'RETRY_BACKOFF_MS', 2000)
        self.retry_backoff_seconds = retry_backoff_ms / 1000

        # Explicit, fail-fast producer config. kafka-python's own defaults are
        # what caused the 60s hang: max_block_ms defaults to 60000ms and
        # delivery_timeout_ms to 120000ms, neither of which was ever set.
        self.producer_config = dict(getattr(settings, 'KAFKA_PRODUCER_CONFIG', {}))

        self.producer = None
        self._ensure_producer()

    def _ensure_producer(self):
        if self.producer is not None:
            return True

        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                **self.producer_config,
            )
            logger.info("Kafka producer initialized")
            return True
        except Exception as e:
            logger.warning(f"Kafka not available: {e}")
            self.producer = None
            return False

    def send_with_retry(self, topic, message, dlq_topic=None, task_id=None):
        """
        Non-blocking entry point for the request path: hands the actual publish
        (with retries) off to a background thread and returns immediately. Used
        for a brand-new event, so failure creates a new DLQ row.
        """
        _executor.submit(self._send_with_retry_sync, topic, message, task_id, None)
        return True

    def send_with_retry_sync(self, topic, message, task_id=None, dlq_entry_id=None):
        """
        Blocking publish-with-retry, used by the DLQ recovery worker and the
        manual "reprocess" admin action. When `dlq_entry_id` is given, failure
        updates that existing row in place instead of creating a new one.
        """
        return self._send_with_retry_sync(topic, message, task_id, dlq_entry_id)

    def _send_with_retry_sync(self, topic, message, task_id=None, dlq_entry_id=None):
        if task_id is None:
            task_id = message.get('task_id')

        if not self._ensure_producer():
            logger.warning(f"Kafka down, saving to DLQ: {topic}")
            self._record_failure(topic, message, "Kafka is down", "ConnectionError", task_id, dlq_entry_id)
            return False

        last_error = None
        last_exception_type = None

        for attempt in range(1, self.max_retries + 1):
            try:
                future = self.producer.send(topic, value=message)
                future.get(timeout=self.producer_config.get('request_timeout_ms', 5000) / 1000)
                logger.info(f"Sent to {topic} (task_id={task_id})")
                if dlq_entry_id:
                    self._mark_dlq_resolved(dlq_entry_id)
                return True

            except Exception as e:
                last_error = str(e)
                last_exception_type = type(e).__name__
                logger.warning(f"Attempt {attempt}/{self.max_retries} failed for {topic}: {last_error}")

                if attempt < self.max_retries:
                    time.sleep(self.retry_backoff_seconds)

        logger.warning(f"All retries failed, saving to DLQ: {topic}")
        self._record_failure(topic, message, last_error, last_exception_type, task_id, dlq_entry_id)
        return False

    def _record_failure(self, topic, message, error, exception_type, task_id, dlq_entry_id):
        """
        Route a publish failure to the DLQ. If this failure belongs to an
        existing DLQ row being retried, update that row in place (increment
        retry_count, refresh error/status) - never create a second row for the
        same event. Only a brand-new failure (no dlq_entry_id yet) creates one.
        """
        if dlq_entry_id:
            self.update_dlq_entry(dlq_entry_id, error, exception_type)
        else:
            self.save_to_dlq_database(topic, message, error, exception_type=exception_type, task_id=task_id)

    def reprocess_pending_dlq_entries(self):
        """Replay pending DLQ entries to their original topics when Kafka is available."""
        from analytics.models import DLQLog

        pending_ids = list(
            DLQLog.objects.filter(status='pending').order_by('created_at').values_list('id', flat=True)
        )
        processed = 0

        for entry_id in pending_ids:
            # Atomic conditional claim: if another worker already flipped this
            # row out of 'pending', this UPDATE affects 0 rows and we skip it.
            # (A DB-agnostic stand-in for SELECT ... FOR UPDATE SKIP LOCKED,
            # which SQLite - this project's DB - does not support.)
            claimed = DLQLog.objects.filter(id=entry_id, status='pending').update(status='processing')
            if not claimed:
                continue
            entry = DLQLog.objects.get(id=entry_id)

            success = self.send_with_retry_sync(
                topic=entry.original_topic,
                message=entry.original_message,
                task_id=entry.task_id,
                dlq_entry_id=entry.id,
            )
            # Success/failure status updates for this row happen inside
            # _send_with_retry_sync (_mark_dlq_resolved / update_dlq_entry) -
            # never touch the row again here, or every failed attempt would
            # both update it AND (if it also created a row on failure) double
            # up. That double-write was the original bug: one failed task
            # publish could balloon into a dozen DLQ rows, and each got
            # replayed to Kafka once recovered, which is what inflated
            # notification/analytics counts downstream.
            if success:
                processed += 1

        return processed

    def save_to_dlq_database(self, original_topic, message, error, exception_type=None, task_id=None):
        """Create a new DLQ row for a brand-new failure (no existing row to update)."""
        try:
            from analytics.models import DLQLog

            dlq_entry = DLQLog.objects.create(
                original_topic=original_topic,
                original_message=message,
                task_id=task_id,
                event_id=message.get('event_id'),
                error=(error or '')[:500],
                exception_type=exception_type,
                retry_count=0,
                max_retries=self.max_retries,
                status='pending',
            )

            logger.info(f"DLQ entry created (ID: {dlq_entry.id}, topic: {original_topic}, error: {(error or '')[:100]})")
            return True

        except Exception as e:
            logger.error(f"CRITICAL: Failed to save DLQ entry: {e}")
            return False

    def update_dlq_entry(self, dlq_entry_id, error, exception_type):
        """Update an existing DLQ row in place after another failed retry - never inserts a new row."""
        from analytics.models import DLQLog

        try:
            entry = DLQLog.objects.get(id=dlq_entry_id)
        except DLQLog.DoesNotExist:
            logger.error(f"CRITICAL: DLQ entry {dlq_entry_id} vanished during retry")
            return False

        entry.retry_count += 1
        entry.error = (error or '')[:500]
        entry.exception_type = exception_type
        entry.status = 'pending' if entry.retry_count < entry.max_retries else 'failed'
        entry.save(update_fields=['retry_count', 'error', 'exception_type', 'status', 'updated_at'])
        return True

    def _mark_dlq_resolved(self, dlq_entry_id):
        from analytics.models import DLQLog

        DLQLog.objects.filter(id=dlq_entry_id).update(status='resolved', resolved_at=timezone.now())


# Global producer instance, shared across requests in this process.
producer = KafkaProducerWithDLQ()


def _build_task_message(task, extra, request=None):
    message = {
        'event_id': str(uuid.uuid4()),
        'task_id': task.id,
        'employee': task.created_by.username,
        'title': task.title,
        **extra,
    }
    if request:
        message['ip_address'] = request.META.get('REMOTE_ADDR')
        message['user_agent'] = request.META.get('HTTP_USER_AGENT')
    return message


def send_task_created(task, request=None):
    message = _build_task_message(task, {
        'status': task.status,
        'description': task.description,
        'created_at': str(task.created_at),
    }, request)

    return producer.send_with_retry(
        topic=get_topic_name('task_created', 'task-created'),
        message=message,
        dlq_topic=get_topic_name('task_dlq', 'task-dlq'),
        task_id=task.id,
    )


def send_task_approved(task, request=None):
    message = _build_task_message(task, {
        'status': 'Approved',
        'approved_by': task.approved_by.username if task.approved_by else 'Admin',
        'comment': task.approval_comment,
    }, request)

    return producer.send_with_retry(
        topic=get_topic_name('task_approved', 'task-approved'),
        message=message,
        dlq_topic=get_topic_name('task_dlq', 'task-dlq'),
        task_id=task.id,
    )


def send_task_rejected(task, request=None):
    message = _build_task_message(task, {
        'status': 'Rejected',
        'rejected_by': task.approved_by.username if task.approved_by else 'Admin',
        'comment': task.approval_comment,
    }, request)

    return producer.send_with_retry(
        topic=get_topic_name('task_rejected', 'task-rejected'),
        message=message,
        dlq_topic=get_topic_name('task_dlq', 'task-dlq'),
        task_id=task.id,
    )
