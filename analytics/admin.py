from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.utils.html import format_html
from .models import AnalyticsLog, DLQLog

@admin.register(AnalyticsLog)
class AnalyticsLogAdmin(admin.ModelAdmin):
    """
    Admin configuration for Analytics Log model
    """
    list_display = ('id', 'event_type', 'task_title', 'employee_name', 'status', 'created_at')
    list_filter = ('event_type', 'status', 'created_at')
    search_fields = ('task_title', 'employee_name', 'task_id')
    ordering = ('-created_at',)
    
    # Fields for detail view
    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'task_id', 'task_title', 'employee_name', 'status')
        }),
        ('Additional Information', {
            'fields': ('ip_address', 'user_agent', 'session_id'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Read-only fields
    readonly_fields = ('created_at', 'processed_at')
    
    # List view customization
    list_display_links = ('id', 'task_title')
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    # Actions
    actions = ['export_selected_as_csv']
    
    def export_selected_as_csv(self, request, queryset):
        """Export selected analytics logs as CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="analytics_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Event Type', 'Task ID', 'Task Title', 'Employee', 'Status', 'Created At', 'IP Address'])
        
        for log in queryset:
            writer.writerow([
                log.get_event_type_display(),
                log.task_id,
                log.task_title,
                log.employee_name,
                log.status,
                log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                log.ip_address or 'N/A'
            ])
        
        self.message_user(request, f'Exported {queryset.count()} records.')
        return response
    export_selected_as_csv.short_description = "Export selected as CSV"
    
    def get_queryset(self, request):
        """Optimize query"""
        return super().get_queryset(request)
    
    def has_add_permission(self, request):
        """Disable adding analytics logs from admin"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing analytics logs"""
        return False


@admin.register(DLQLog)
class DLQLogAdmin(admin.ModelAdmin):
    """
    Admin configuration for DLQ Log model
    """
    list_display = ('id', 'original_topic', 'status', 'retry_count', 'created_at', 'error_preview')
    list_filter = ('status', 'original_topic', 'created_at')
    search_fields = ('original_topic', 'error', 'original_message')
    ordering = ('-created_at',)
    
    # Fields for detail view
    fieldsets = (
        ('DLQ Information', {
            'fields': ('original_topic', 'original_message', 'error')
        }),
        ('Retry Status', {
            'fields': ('status', 'retry_count', 'max_retries')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Read-only fields
    readonly_fields = ('created_at', 'updated_at')
    
    # List view customization
    list_display_links = ('id', 'original_topic')
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    # Actions
    actions = ['mark_as_resolved', 'mark_as_failed', 'reset_retry']
    
    def error_preview(self, obj):
        """Display error preview"""
        return obj.error[:50] + '...' if len(obj.error) > 50 else obj.error
    error_preview.short_description = 'Error'
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'pending': 'warning',
            'processing': 'info',
            'resolved': 'success',
            'failed': 'danger'
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            colors.get(obj.status, 'secondary'),
            obj.status.upper()
        )
    status_badge.short_description = 'Status'
    
    def mark_as_resolved(self, request, queryset):
        """Bulk action: Mark as resolved"""
        from django.utils import timezone
        updated = queryset.update(status='resolved', resolved_at=timezone.now())
        self.message_user(request, f'{updated} DLQ entries marked as resolved.')
    mark_as_resolved.short_description = "Mark as Resolved"
    
    def mark_as_failed(self, request, queryset):
        """Bulk action: Mark as failed"""
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} DLQ entries marked as failed.')
    mark_as_failed.short_description = "Mark as Failed"
    
    def reset_retry(self, request, queryset):
        """Bulk action: Reset retry count"""
        updated = queryset.update(retry_count=0, status='pending')
        self.message_user(request, f'{updated} DLQ entries reset for retry.')
    reset_retry.short_description = "Reset Retry Count"
    
    def get_queryset(self, request):
        """Optimize query"""
        return super().get_queryset(request)
    
    def has_add_permission(self, request):
        """Disable adding DLQ logs from admin"""
        return False