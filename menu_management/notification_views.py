from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.urls import path
from .notification_service import NotificationService, NotificationConsumer
from .notification_models import Notification, NotificationPreference
from orders.models import Order
import json

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
@user_passes_test(is_admin)
def notification_center(request):
    """Notification center for staff"""
    notification_service = NotificationService()
    
    # Get unread notifications
    unread_notifications = notification_service.get_unread_notifications(request.user, limit=20)
    
    # Get recent notifications (all)
    all_notifications = Notification.objects.filter(
        recipient=request.user
    ).exclude(
        expires_at__lt=timezone.now()
    ).order_by('-created_at')[:50]
    
    # Get user preferences
    preferences, created = NotificationPreference.objects.get_or_create(user=request.user)
    
    context = {
        'unread_notifications': unread_notifications,
        'all_notifications': all_notifications,
        'preferences': preferences,
        'unread_count': len(unread_notifications),
    }
    return render(request, 'menu_management/notification_center.html', context)

@login_required
@user_passes_test(is_admin)
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    notification_service = NotificationService()
    success = notification_service.mark_notification_read(notification_id, request.user)
    
    if success:
        return JsonResponse({
            'success': True,
            'message': 'Notification marked as read'
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Notification not found'
        })

@login_required
@user_passes_test(is_admin)
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    unread_notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    )
    
    count = 0
    for notification in unread_notifications:
        notification.mark_as_read()
        count += 1
    
    return JsonResponse({
        'success': True,
        'message': f'Marked {count} notifications as read'
    })

@login_required
@user_passes_test(is_admin)
def update_notification_preferences(request):
    """Update notification preferences"""
    preferences, created = NotificationPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        preferences.order_notifications = request.POST.get('order_notifications') == 'true'
        preferences.station_alerts = request.POST.get('station_alerts') == 'true'
        preferences.inventory_alerts = request.POST.get('inventory_alerts') == 'true'
        preferences.system_alerts = request.POST.get('system_alerts') == 'true'
        
        preferences.in_app_notifications = request.POST.get('in_app_notifications') == 'true'
        preferences.email_notifications = request.POST.get('email_notifications') == 'true'
        preferences.sound_notifications = request.POST.get('sound_notifications') == 'true'
        
        preferences.min_priority_level = request.POST.get('min_priority_level', 'medium')
        preferences.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Preferences updated successfully'
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_admin)
def send_test_notification(request):
    """Send a test notification"""
    if request.method == 'POST':
        notification_service = NotificationService()
        
        success = notification_service.send_notification(
            recipient=request.user,
            notification_type='system_alert',
            title='🧪 Test Notification',
            message='This is a test notification to verify the notification system is working correctly.',
            priority='medium',
            data={'test': True}
        )
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Test notification sent successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to send test notification'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_admin)
def get_notification_count(request):
    """Get unread notification count"""
    notification_service = NotificationService()
    unread_count = len(notification_service.get_unread_notifications(request.user, limit=100))
    
    return JsonResponse({
        'unread_count': unread_count
    })

@login_required
@user_passes_test(is_admin)
def notification_details(request, notification_id):
    """Get detailed information about a specific notification"""
    try:
        notification_service = NotificationService()
        notification = notification_service.get_notification_by_id(notification_id, request.user)
        
        if not notification:
            return JsonResponse({
                'success': False,
                'message': 'Notification not found'
            }, status=404)
        
        # Format the notification data
        notification_data = {
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'notification_type': notification.notification_type,
            'notification_type_display': notification.get_notification_type_display(),
            'priority': notification.priority,
            'is_read': notification.is_read,
            'created_at': notification.created_at.isoformat(),
            'created_at_formatted': notification.created_at.strftime('%B %d, %Y at %I:%M %p'),
            'expires_at': notification.expires_at.isoformat() if notification.expires_at else None,
            'expires_at_formatted': notification.expires_at.strftime('%B %d, %Y at %I:%M %p') if notification.expires_at else None,
            'data': notification.data or {},
            'recipient_name': notification.recipient.get_full_name() or notification.recipient.username,
        }
        
        return JsonResponse({
            'success': True,
            'notification': notification_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error loading notification details: {str(e)}'
        }, status=500)

# Integration with order management
def send_order_notification_signal(sender, instance, created, **kwargs):
    """Signal handler for order notifications"""
    if created:
        notification_service = NotificationService()
        notification_service.send_order_notification(instance, 'order_received')

def send_order_status_change_signal(sender, instance, **kwargs):
    """Signal handler for order status changes"""
    notification_service = NotificationService()
    
    # Determine notification type based on status
    status_notifications = {
        'confirmed': 'order_started',
        'preparing': 'order_started',
        'ready': 'order_ready',
        'completed': 'order_completed',
        'cancelled': 'order_completed'
    }
    
    notification_type = status_notifications.get(instance.status)
    if notification_type:
        notification_service.send_order_notification(instance, notification_type)

# WebSocket routing (to be added to asgi.py)
websocket_urlpatterns = [
    path('ws/notifications/', NotificationConsumer.as_asgi()),
]
