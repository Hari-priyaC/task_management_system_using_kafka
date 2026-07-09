from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Admin configuration for Custom User model
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'department', 'is_active')
    list_filter = ('role', 'department', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)
    
    # Fields to display in list view
    list_display_links = ('username', 'email')
    
    # Fields for detail view
    fieldsets = (
        ('Login Information', {
            'fields': ('username', 'password')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Work Information', {
            'fields': ('role', 'department')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    # Fields for adding new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'department'),
        }),
    )
    
    # Actions for bulk operations
    actions = ['make_admin', 'make_employee', 'activate_users', 'deactivate_users']
    
    def make_admin(self, request, queryset):
        """Bulk action: Make selected users admin"""
        updated = queryset.update(role='admin')
        self.message_user(request, f'{updated} users promoted to Admin.')
    make_admin.short_description = "Make selected users Admin"
    
    def make_employee(self, request, queryset):
        """Bulk action: Make selected users employee"""
        updated = queryset.update(role='employee')
        self.message_user(request, f'{updated} users changed to Employee.')
    make_employee.short_description = "Make selected users Employee"
    
    def activate_users(self, request, queryset):
        """Bulk action: Activate selected users"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users activated.')
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        """Bulk action: Deactivate selected users"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated.')
    deactivate_users.short_description = "Deactivate selected users"