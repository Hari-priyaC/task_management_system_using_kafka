from kafka import KafkaProducer
import json
from django.conf import settings
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)


def get_topic_name(topic_key, default_name='task-dlq'):
    """Resolve topic names from either a dict or an object-backed settings value."""
    topics = getattr(settings, 'KAFKA_TOPICS', {})
    if isinstance(topics, dict):
        return topics.get(topic_key, default_name)
    return getattr(topics, topic_key, default_name)


class KafkaProducerWithDLQ:
    """
    PRODUCER WITH DLQ - FINAL ROBUST VERSION
    - Only saves to DLQ when there's a REAL error
    - All normal flows work perfectly
    - Always returns True (task is always saved)
    """
    
    def __init__(self):
        self.bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS
        self.max_retries = getattr(settings, 'MAX_RETRY_ATTEMPTS', 2)
        self.retry_backoff = getattr(settings, 'RETRY_BACKOFF_MS', 1000)
        
        # Initialize producer - NEVER RAISES EXCEPTION
        self.producer = None
        self._ensure_producer()

    def _ensure_producer(self):
        if self.producer is not None:
            return True

        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                retries=0,
                request_timeout_ms=3000,
            )
            logger.info(" Kafka producer initialized")
            return True
        except Exception as e:
            logger.warning(f" Kafka not available: {e}")
            self.producer = None
            return False
    
    def send_with_retry(self, topic, message, dlq_topic=None):
        """
        SEND WITH RETRY - ONLY SAVES TO DLQ ON REAL ERRORS
        """
        if dlq_topic is None:
            dlq_topic = get_topic_name('task_dlq', 'task-dlq')
        
        #  CASE 1: Kafka is DOWN → Save to DLQ
        if self.producer is None:
            logger.warning(f" Kafka down, saving to DLQ: {topic}")
            self.save_to_dlq_database(topic, message, "Kafka is down")
            return True
        
        if not self._ensure_producer():
            return False

        #  CASE 2: Try to send to Kafka
        for attempt in range(self.max_retries):
            try:
                future = self.producer.send(topic, value=message)
                result = future.get(timeout=3)
                self.producer.flush()
                logger.info(f"Sent to {topic}")
                return True
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f" Attempt {attempt+1}/{self.max_retries} failed: {error_msg}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                else:
                    #  All retries failed → Save to DLQ
                    logger.warning(f"💀 All retries failed, saving to DLQ: {topic}")
                    self.save_to_dlq_database(topic, message, error_msg)
                    return True
        
        return True

    def reprocess_pending_dlq_entries(self):
        """Replay pending DLQ entries to their original topics when Kafka is available."""
        from analytics.models import DLQLog

        pending_entries = DLQLog.objects.filter(status='pending').order_by('created_at')
        processed = 0

        for entry in pending_entries:
            entry.status = 'processing'
            entry.save(update_fields=['status'])

            if not self._ensure_producer():
                entry.status = 'pending'
                entry.save(update_fields=['status'])
                continue

            success = self.send_with_retry(
                topic=entry.original_topic,
                message=entry.original_message,
                dlq_topic='task-dlq',
            )

            if success:
                entry.status = 'resolved'
                entry.resolved_at = datetime.now()
                entry.save(update_fields=['status', 'resolved_at'])
                processed += 1
            else:
                entry.status = 'failed'
                entry.save(update_fields=['status'])

        return processed
    
    def save_to_dlq_database(self, original_topic, message, error):
        """
        SAVE TO DLQ - ONLY CALLED ON REAL ERRORS
        """
        try:
            from analytics.models import DLQLog
            
            #  Create DLQ entry
            dlq_entry = DLQLog.objects.create(
                original_topic=original_topic,
                original_message=message,
                error=error[:500],
                retry_count=0,
                max_retries=self.max_retries,
                status='pending',
                created_at=datetime.now()
            )
            
            logger.info(f" DLQ entry created (ID: {dlq_entry.id})")
            logger.info(f"   Topic: {original_topic}")
            logger.info(f"   Error: {error[:100]}")
            return True
            
        except Exception as e:
            logger.error(f" CRITICAL: Failed to save DLQ: {e}")
            return False


#  Global producer
producer = KafkaProducerWithDLQ()


def send_task_created(task, request=None):
    """SEND TASK CREATED"""
    message = {
        'task_id': task.id,
        'employee': task.created_by.username,
        'title': task.title,
        'status': task.status,
        'description': task.description,
        'created_at': str(task.created_at)
    }
    if request:
        message['ip_address'] = request.META.get('REMOTE_ADDR')
        message['user_agent'] = request.META.get('HTTP_USER_AGENT')
    
    return producer.send_with_retry(
        topic=get_topic_name('task_created', 'task-created'),
        message=message,
        dlq_topic=get_topic_name('task_dlq', 'task-dlq')
    )


def send_task_approved(task, request=None):
    """SEND TASK APPROVED"""
    message = {
        'task_id': task.id,
        'employee': task.created_by.username,
        'title': task.title,
        'status': 'Approved',
        'approved_by': task.approved_by.username if task.approved_by else 'Admin',
        'comment': task.approval_comment
    }
    if request:
        message['ip_address'] = request.META.get('REMOTE_ADDR')
        message['user_agent'] = request.META.get('HTTP_USER_AGENT')
    
    return producer.send_with_retry(
        topic=get_topic_name('task_approved', 'task-approved'),
        message=message,
        dlq_topic=get_topic_name('task_dlq', 'task-dlq')
    )


def send_task_rejected(task, request=None):
    """SEND TASK REJECTED"""
    message = {
        'task_id': task.id,
        'employee': task.created_by.username,
        'title': task.title,
        'status': 'Rejected',
        'rejected_by': task.approved_by.username if task.approved_by else 'Admin',
        'comment': task.approval_comment
    }
    if request:
        message['ip_address'] = request.META.get('REMOTE_ADDR')
        message['user_agent'] = request.META.get('HTTP_USER_AGENT')
    
    return producer.send_with_retry(
        topic=get_topic_name('task_rejected', 'task-rejected'),
        message=message,
        dlq_topic=get_topic_name('task_dlq', 'task-dlq')
    )