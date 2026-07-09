from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.analytics_dashboard, name='analytics_dashboard'),
    path('dlq/', views.dlq_dashboard, name='dlq_dashboard'),
    path('dlq/<int:dlq_id>/reprocess/', views.reprocess_dlq, name='reprocess_dlq'),
    path('download/csv/', views.download_csv, name='download_csv'),
    path('download/excel/', views.download_excel, name='download_excel'),
    path('download/json/', views.download_json, name='download_json'),
]