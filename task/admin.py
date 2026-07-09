from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.utils.html import format_html
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """
    Admin configuration for Task model
    """
    list_display = ('id', 'title', 'created_by', 'status', 'created_at', 'status_badge')
    list_filter = ('status', 'created_at', 'created_by')
    search_fields = ('title', 'description', 'created_by__username')
    ordering = ('-created_at',)
    
    # Fields for detail view
    fieldsets = (
        ('Task Information', {
            'fields': ('title', 'description')
        }),
        ('Status & Approval', {
            'fields': ('status', 'approved_by', 'approval_comment')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Read-only fields
    readonly_fields = ('created_at', 'updated_at')
    
    # List view customization
    list_display_links = ('id', 'title')
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    # Actions
    actions = ['approve_tasks', 'reject_tasks', 'mark_as_pending']
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'danger'
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            colors.get(obj.status, 'secondary'),
            obj.status.upper()
        )
    status_badge.short_description = 'Status'
    
    def approve_tasks(self, request, queryset):
        """Bulk action: Approve selected tasks"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        updated = 0
        for task in queryset:
            if task.status == 'pending':
                task.status = 'approved'
                task.approved_by = request.user
                task.save()
                updated += 1
        
        self.message_user(request, f'{updated} tasks approved.')
    approve_tasks.short_description = "Approve selected tasks"
    
    def reject_tasks(self, request, queryset):
        """Bulk action: Reject selected tasks"""
        updated = 0
        for task in queryset:
            if task.status == 'pending':
                task.status = 'rejected'
                task.approved_by = request.user
                task.save()
                updated += 1
        
        self.message_user(request, f'{updated} tasks rejected.')
    reject_tasks.short_description = "Reject selected tasks"
    
    def mark_as_pending(self, request, queryset):
        """Bulk action: Mark tasks as pending"""
        updated = queryset.update(status='pending')
        self.message_user(request, f'{updated} tasks marked as pending.')
    mark_as_pending.short_description = "Mark as Pending"
    
    # Inline views for related data
    def get_queryset(self, request):
        """Optimize query with select_related"""
        return super().get_queryset(request).select_related('created_by', 'approved_by')
    
    # Save method with logging
    def save_model(self, request, obj, form, change):
        """Log when task is saved"""
        if not obj.pk:
            # New task
            obj.created_by = request.user
            super().save_model(request, obj, form, change)
        else:
            # Existing task
            old_obj = Task.objects.get(pk=obj.pk)
            if old_obj.status != obj.status:
                # Status changed
                obj.approved_by = request.user if obj.status != 'pending' else None
            super().save_model(request, obj, form, change)