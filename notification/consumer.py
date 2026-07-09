import os
import sys

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
from datetime import datetime

print(" Notification Consumer Starting...")

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
    print("Connected to Kafka")
    print(" Waiting for notifications...")
    print(consumer,"consumerrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr")
    
    for message in consumer:
        data = message.value
        print(data,"dataaaaaaaaaaaaaaaaaaaaaaaaa", message.value)
        
        try:
            employee = CustomUser.objects.get(username=data.get('employee'))
            print(employee,"employeessssssssssssssssssssssss")
            
            notification = Notification.objects.create(
                user=employee,
                title=f"Task {data.get('status')}",
                message=f"Your task '{data.get('title')}' has been {data.get('status')}!",
                task_id=data.get('task_id'),
                is_read=False,
                created_at=datetime.now()
            )
            
            print(f" Notification saved for {employee.username}")
            
        except CustomUser.DoesNotExist:
            print(f" User {data.get('employee')} not found!")
        except Exception as e:
            print(f" Error: {e}")
            
except KeyboardInterrupt:
    print("\n Stopped")
except Exception as e:
    print(f" Error: {e}")