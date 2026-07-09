from django.shortcuts import render
from django.db import models

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q
from task.models import Task
from .models import AnalyticsLog, DLQLog
import csv
import json
from datetime import datetime, timedelta
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment


@login_required
def analytics_dashboard(request):
    """Analytics dashboard"""
    if not request.user.is_admin():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    days = int(request.GET.get('days', 30))
    employee_filter = request.GET.get('employee', '')
    start_date = datetime.now() - timedelta(days=days)
    
    logs = AnalyticsLog.objects.filter(created_at__gte=start_date)
    if employee_filter:
        logs = logs.filter(employee_name=employee_filter)
    
    total_tasks = logs.count()
    total_created = logs.filter(event_type='task_created').count()
    total_approved = logs.filter(event_type='task_approved').count()
    total_rejected = logs.filter(event_type='task_rejected').count()
    
    success_rate = 0
    if total_approved + total_rejected > 0:
        success_rate = round((total_approved / (total_approved + total_rejected)) * 100, 2)
    
    employee_stats = logs.values('employee_name').annotate(
        total=Count('id'),
        approved=Count('id', filter=Q(event_type='task_approved')),
        rejected=Count('id', filter=Q(event_type='task_rejected'))
    ).order_by('-total')
    
    daily_trends = logs.filter(
        created_at__gte=datetime.now() - timedelta(days=7)
    ).annotate(
        date=models.functions.TruncDate('created_at')
    ).values('date').annotate(
        total=Count('id'),
        approved=Count('id', filter=Q(event_type='task_approved')),
        rejected=Count('id', filter=Q(event_type='task_rejected'))
    ).order_by('date')
    
    recent_logs = logs[:50]
    all_employees = AnalyticsLog.objects.values_list('employee_name', flat=True).distinct()
    
    context = {
        'total_tasks': total_tasks,
        'total_created': total_created,
        'total_approved': total_approved,
        'total_rejected': total_rejected,
        'success_rate': success_rate,
        'employee_stats': employee_stats,
        'daily_trends': list(daily_trends),
        'recent_logs': recent_logs,
        'all_employees': all_employees,
        'selected_employee': employee_filter,
        'selected_days': days,
    }
    
    return render(request, 'analytics_dashboard.html', context)


# ⭐ NEW: DLQ Dashboard
@login_required
def dlq_dashboard(request):
    """
    Dashboard to monitor Dead Letter Queue
    """
    if not request.user.is_admin():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Get DLQ statistics
    total_dlq = DLQLog.objects.count()
    pending_dlq = DLQLog.objects.filter(status='pending').count()
    processing_dlq = DLQLog.objects.filter(status='processing').count()
    resolved_dlq = DLQLog.objects.filter(status='resolved').count()
    failed_dlq = DLQLog.objects.filter(status='failed').count()
    
    # Get recent DLQ entries
    recent_dlq = DLQLog.objects.all().order_by('-created_at')[:30]
    
    context = {
        'total_dlq': total_dlq,
        'pending_dlq': pending_dlq,
        'processing_dlq': processing_dlq,
        'resolved_dlq': resolved_dlq,
        'failed_dlq': failed_dlq,
        'recent_dlq': recent_dlq,
    }
    
    return render(request, 'dlq_dashboard.html', context)


# ⭐ NEW: Reprocess DLQ Entry
@login_required
def reprocess_dlq(request, dlq_id):
    """
    Manually reprocess a DLQ entry
    """
    if not request.user.is_admin():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        dlq_entry = DLQLog.objects.get(id=dlq_id)
        
        # Update status
        dlq_entry.status = 'processing'
        dlq_entry.save()
        
        # Trigger reprocessing via Kafka
        from task.producer import KafkaProducerWithDLQ
        producer = KafkaProducerWithDLQ()
        
        # Send message back to original topic
        success = producer.send_with_retry(
            topic=dlq_entry.original_topic,
            message=dlq_entry.original_message,
            dlq_topic='task-dlq'
        )
        
        if success:
            dlq_entry.status = 'resolved'
            dlq_entry.resolved_at = datetime.now()
            dlq_entry.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Message reprocessed successfully'
            })
        else:
            dlq_entry.status = 'failed'
            dlq_entry.save()
            
            return JsonResponse({
                'success': False,
                'message': 'Reprocessing failed. Check DLQ.'
            }, status=500)
            
    except DLQLog.DoesNotExist:
        return JsonResponse({'error': 'DLQ entry not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Download functions
@login_required
def download_csv(request):
    if not request.user.is_admin():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="analytics_data.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Event Type', 'Task ID', 'Task Title', 'Employee', 'Status', 'Created At', 'IP Address'])
    
    logs = AnalyticsLog.objects.all().order_by('-created_at')
    for log in logs:
        writer.writerow([
            log.get_event_type_display(),
            log.task_id,
            log.task_title,
            log.employee_name,
            log.status,
            log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            log.ip_address or 'N/A'
        ])
    
    return response


@login_required
def download_excel(request):
    if not request.user.is_admin():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "Analytics Data"
    
    headers = ['Event Type', 'Task ID', 'Task Title', 'Employee', 'Status', 'Created At', 'IP Address']
    for col, header in enumerate(headers, 1):
        cell = ws1.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")
    
    logs = AnalyticsLog.objects.all().order_by('-created_at')
    for row, log in enumerate(logs, 2):
        ws1.cell(row=row, column=1, value=log.get_event_type_display())
        ws1.cell(row=row, column=2, value=log.task_id)
        ws1.cell(row=row, column=3, value=log.task_title)
        ws1.cell(row=row, column=4, value=log.employee_name)
        ws1.cell(row=row, column=5, value=log.status)
        ws1.cell(row=row, column=6, value=log.created_at.strftime('%Y-%m-%d %H:%M:%S'))
        ws1.cell(row=row, column=7, value=log.ip_address or 'N/A')
    
    for column in ws1.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 30)
        ws1.column_dimensions[column_letter].width = adjusted_width
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="analytics_data.xlsx"'
    wb.save(response)
    return response


@login_required
def download_json(request):
    if not request.user.is_admin():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    logs = AnalyticsLog.objects.all().order_by('-created_at')
    data = []
    for log in logs:
        data.append({
            'event_type': log.get_event_type_display(),
            'task_id': log.task_id,
            'task_title': log.task_title,
            'employee': log.employee_name,
            'status': log.status,
            'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'ip_address': log.ip_address
        })
    
    response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="analytics_data.json"'
    return response