from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('employee-dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('api/employees/', views.get_employees, name='get_employees'),
    path('api/employees/create/', views.create_employee, name='create_employee'),
    path('api/employees/<int:user_id>/update/', views.update_employee, name='update_employee'),
    path('api/employees/<int:user_id>/delete/', views.delete_employee, name='delete_employee'),
    path('api/users/<int:user_id>/change-role/', views.change_role, name='change_role'),
]