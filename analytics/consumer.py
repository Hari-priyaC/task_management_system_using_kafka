import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from kafka import KafkaConsumer
import json
from django.conf import settings
from analytics.models import AnalyticsLog

print(" Analytics Consumer Started...")

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
    print(" Connected to Kafka")
    print(" Logging analytics...")
    
    for message in consumer:
        print(f" Received message from topic: {message.topic}")
        try:
            data = message.value
            topic = message.topic
            
            event_type_map = {
                'task-created': 'task_created',
                'task-approved': 'task_approved',
                'task-rejected': 'task_rejected'
            }
            
            AnalyticsLog.objects.create(
                event_type=event_type_map.get(topic, 'unknown'),
                task_id=data.get('task_id'),
                task_title=data.get('title'),
                employee_name=data.get('employee'),
                status=data.get('status', 'pending'),
                ip_address=data.get('ip_address', None),
                user_agent=data.get('user_agent', None)
            )
            
            print(f" Analytics logged: {topic}")
            
        except Exception as e:
            print(f" Error: {e}")
            
except KeyboardInterrupt:
    print("\n Stopped")
except Exception as e:
    print(f" Error: {e}")