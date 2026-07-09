from django.urls import path
from . import views

urlpatterns = [
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('<int:notification_id>/read/', views.mark_as_read, name='mark_as_read'),
    path('read-all/', views.mark_all_as_read, name='mark_all_as_read'),
    path('unread-count/', views.get_unread_count, name='get_unread_count'),
]