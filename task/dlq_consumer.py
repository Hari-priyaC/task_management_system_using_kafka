import os
import sys
import time

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from task.producer import KafkaProducerWithDLQ

print("🔍 DLQ Consumer Starting...")

try:
    producer = KafkaProducerWithDLQ()
    print(" Monitoring DLQ database for pending messages...")

    while True:
        processed = producer.reprocess_pending_dlq_entries()
        if processed:
            print(f" Replayed {processed} DLQ entries")
        time.sleep(5)

except KeyboardInterrupt:
    print("\n Stopped")
except Exception as e:
    print(f" Error: {e}")