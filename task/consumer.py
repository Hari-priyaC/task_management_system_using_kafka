from kafka import KafkaConsumer
import json
from django.conf import settings
import logging
import sys
import os


project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from task.models import Task
from notification.models import Notification
from accounts.models import CustomUser

logger = logging.getLogger(__name__)


class TaskConsumer:
    """Task Consumer with DLQ support"""
    
    def __init__(self):
        self.topic = settings.KAFKA_TOPICS['task_created']
        
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                auto_offset_reset='earliest',
                group_id='admin-group',
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            logger.info(f" Task consumer started on topic: {self.topic}")
        except Exception as e:
            logger.error(f" Failed to start consumer: {e}")
            self.consumer = None
    
    def process_message(self, message):
        """Process incoming message"""
        try:
            task_data = message.value
            
            print("\n" + "="*60)
            print(" NEW TASK CREATED!")
            print("="*60)
            print(f" Task Title  : {task_data['title']}")
            print(f" Employee    : {task_data['employee']}")
            print(f"Status      : {task_data['status']}")
            print(f"Description : {task_data['description']}")
            print("="*60 + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f" Error processing message: {e}")
            return False
    
    def start(self):
        """Start consuming messages"""
        if self.consumer is None:
            print(" Consumer not initialized")
            return
        
        print(f" Waiting for new tasks on topic: {self.topic}...")
        print("Press Ctrl+C to stop")
        
        try:
            for message in self.consumer:
                self.process_message(message)
                
        except KeyboardInterrupt:
            print("\n Consumer stopped by user")
        except Exception as e:
            logger.error(f" Consumer error: {e}")
        finally:
            if self.consumer:
                self.consumer.close()


if __name__ == "__main__":
    consumer = TaskConsumer()
    consumer.start()