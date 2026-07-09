from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings

class AnalyticsLog(models.Model):
    EVENT_TYPES = (
        ('task_created', 'Task Created'),
        ('task_approved', 'Task Approved'),
        ('task_rejected', 'Task Rejected'),
    )
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    task_id = models.IntegerField()
    task_title = models.CharField(max_length=200)
    employee_name = models.CharField(max_length=150)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    session_id = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.event_type} - {self.task_title} by {self.employee_name}"
    
    class Meta:
        ordering = ['-created_at']


#  NEW: DLQ Tracking Model
class DLQLog(models.Model):
    """
    Tracks messages sent to Dead Letter Queue
    """
    original_topic = models.CharField(max_length=100)
    original_message = models.JSONField()
    error = models.TextField()
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('resolved', 'Resolved'),
            ('failed', 'Failed')
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"DLQ Entry: {self.original_topic} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']