import os
import sys
import logging

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from kafka import KafkaConsumer
import json
from django.conf import settings
from accounts.models import CustomUser
from notification.models import Notification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _notify(user, title, message, task_id, dedup_key):
    fields = dict(user=user, title=title, message=message, task_id=task_id, is_read=False)

    if dedup_key:
        # get_or_create on the unique event_id makes this idempotent: if the
        # same Kafka message is redelivered (rebalance, DLQ replay of an
        # event that actually went through, at-least-once commit semantics),
        # it's a no-op instead of a second row.
        _, created = Notification.objects.get_or_create(event_id=dedup_key, defaults=fields)
        return created
    else:
        # Legacy message with no event_id (produced before this field
        # existed) - can't dedupe it, so just create it as before.
        Notification.objects.create(event_id=None, **fields)
        return True


def process_message(message):
    data = message.value
    event_id = data.get('event_id')
    task_id = data.get('task_id')

    try:
        if message.topic == 'task-created':
            # A new task needs approval - notify every admin, not the
            # employee who just created it (they already know).
            for admin in CustomUser.objects.filter(role='admin'):
                dedup_key = f"{event_id}:a{admin.id}" if event_id else None
                created = _notify(
                    user=admin,
                    title="New Task Pending Approval",
                    message=f"{data.get('employee')} created a new task: '{data.get('title')}'",
                    task_id=task_id,
                    dedup_key=dedup_key,
                )
                logger.info(f"{'Notified' if created else 'Duplicate ignored'}: admin={admin.username} task_id={task_id}")

        else:
            # task-approved / task-rejected - notify the employee who
            # created the task about the outcome.
            employee = CustomUser.objects.get(username=data.get('employee'))
            created = _notify(
                user=employee,
                title=f"Task {data.get('status')}",
                message=f"Your task '{data.get('title')}' has been {data.get('status')}!",
                task_id=task_id,
                dedup_key=event_id,
            )
            logger.info(f"{'Notified' if created else 'Duplicate ignored'}: employee={employee.username} task_id={task_id}")

    except CustomUser.DoesNotExist:
        logger.warning(f"User {data.get('employee')} not found!")
    except Exception as e:
        logger.error(f"Error processing message: {e}")


def main():
    logger.info("Notification Consumer Starting...")
    try:
        consumer = KafkaConsumer(
            'task-approved',
            'task-rejected',
            'task-created',
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset='earliest',
            group_id='notification-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        logger.info("Connected to Kafka, waiting for notifications...")

        for message in consumer:
            process_message(message)

    except KeyboardInterrupt:
        logger.info("Stopped")
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    main()
