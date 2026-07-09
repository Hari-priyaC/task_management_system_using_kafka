from django.shortcuts import render

# Create your views here.
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification

@login_required
def get_notifications(request):
    notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-id')
    print(notifications,"notifications")
    
    notif_list = []
    for notif in notifications:
        notif_list.append({
            'id': notif.id,
            'title': notif.title,
            'message': notif.message,
            'task_id': notif.task_id,
            'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_read': notif.is_read
        })
    
    return JsonResponse({
        'count': notifications.count(),
        'notifications': notif_list
    })

@login_required
def mark_as_read(request, notification_id):
    if request.method not in ['POST', 'GET']:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})

@login_required
def mark_all_as_read(request):
    if request.method not in ['POST', 'GET']:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})

@login_required
def get_unread_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})