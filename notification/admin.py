from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.utils.html import format_html
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin configuration for Notification model
    """
    list_display = ('id', 'user', 'title', 'is_read', 'created_at', 'message_preview')
    list_filter = ('is_read', 'created_at', 'user')
    search_fields = ('title', 'message', 'user__username', 'user__email')
    ordering = ('-created_at',)
    
    # Fields for detail view
    fieldsets = (
        ('Notification Information', {
            'fields': ('user', 'title', 'message', 'task_id')
        }),
        ('Status', {
            'fields': ('is_read',)
        }),
        ('Audit Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    # Read-only fields
    readonly_fields = ('created_at',)
    
    # List view customization
    list_display_links = ('id', 'title')
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    # Actions
    actions = ['mark_as_read', 'mark_as_unread', 'delete_selected']
    
    def message_preview(self, obj):
        """Display message preview"""
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'
    
    def mark_as_read(self, request, queryset):
        """Bulk action: Mark notifications as read"""
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = "Mark as Read"
    
    def mark_as_unread(self, request, queryset):
        """Bulk action: Mark notifications as unread"""
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notifications marked as unread.')
    mark_as_unread.short_description = "Mark as Unread"
    
    def get_queryset(self, request):
        """Optimize query with select_related"""
        return super().get_queryset(request).select_related('user')
    
    def has_add_permission(self, request):
        """Disable adding notifications from admin"""
        return False