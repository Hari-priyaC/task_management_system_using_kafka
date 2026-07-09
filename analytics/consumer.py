import os
import sys
import logging

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from kafka import KafkaConsumer
import json
from django.conf import settings
from analytics.models import AnalyticsLog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EVENT_TYPE_MAP = {
    'task-created': 'task_created',
    'task-approved': 'task_approved',
    'task-rejected': 'task_rejected',
}


def process_message(message):
    try:
        data = message.value
        topic = message.topic
        event_id = data.get('event_id')

        fields = dict(
            event_type=EVENT_TYPE_MAP.get(topic, 'unknown'),
            task_id=data.get('task_id'),
            task_title=data.get('title'),
            employee_name=data.get('employee'),
            status=data.get('status', 'pending'),
            ip_address=data.get('ip_address', None),
            user_agent=data.get('user_agent', None),
        )

        if event_id:
            # Dedupe on event_id: the same event can be redelivered on
            # rebalance/DLQ replay - without this, every redelivery
            # inflated dashboard event counts.
            log, created = AnalyticsLog.objects.get_or_create(event_id=event_id, defaults=fields)
            logger.info(f"{'Logged' if created else 'Duplicate ignored'}: {topic} (event_id={event_id})")
        else:
            AnalyticsLog.objects.create(event_id=None, **fields)
            logger.warning(f"Analytics logged without event_id for task_id={data.get('task_id')}")

    except Exception as e:
        logger.error(f"Error: {e}")


def main():
    logger.info("Analytics Consumer Started...")
    try:
        consumer = KafkaConsumer(
            'task-created',
            'task-approved',
            'task-rejected',
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset='earliest',
            group_id='analytics-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        logger.info("Connected to Kafka, logging analytics...")

        for message in consumer:
            process_message(message)

    except KeyboardInterrupt:
        logger.info("Stopped")
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    main()
