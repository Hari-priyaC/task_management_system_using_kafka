from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_task, name='create_task'),
    path('tasks/', views.get_tasks, name='get_tasks'),
    path('<int:task_id>/approve/', views.approve_task, name='approve_task'),
    path('pending/', views.get_pending_tasks, name='get_pending_tasks'),
]