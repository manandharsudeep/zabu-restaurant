from django.utils import timezone
from django.contrib.auth.models import User
from channels.layers import get_channel_layer
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync
from .notification_models import Notification, NotificationPreference, NotificationTemplate
from orders.models import Order
import json
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """Real-time notification service"""
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def send_notification(self, recipient, notification_type, title, message, 
                         priority='medium', data=None, expires_minutes=60):
        """Send a notification to a specific user"""
        try:
            # Check user preferences
            preferences = self._get_user_preferences(recipient)
            if not self._should_send_notification(preferences, notification_type, priority):
                return False
            
            # Create notification
            notification = Notification.objects.create(
                recipient=recipient,
                notification_type=notification_type,
                priority=priority,
                title=title,
                message=message,
                data=data or {},
                expires_at=timezone.now() + timezone.timedelta(minutes=expires_minutes)
            )
            
            # Send via WebSocket
            self._send_websocket_notification(recipient, notification)
            
            # Send via other channels if enabled
            if preferences.email_notifications:
                self._send_email_notification(recipient, notification)
            
            if preferences.sound_notifications:
                self._send_sound_notification(recipient, notification)
            
            return True
        
        except Exception as e:
            logger.error(f"Error sending notification to {recipient.username}: {str(e)}")
            return False
    
    def send_bulk_notification(self, recipients, notification_type, title, message, 
                              priority='medium', data=None, expires_minutes=60):
        """Send notification to multiple users"""
        success_count = 0
        
        for recipient in recipients:
            if self.send_notification(recipient, notification_type, title, message, 
                                   priority, data, expires_minutes):
                success_count += 1
        
        return success_count
    
    def send_order_notification(self, order, notification_type, additional_data=None):
        """Send order-related notifications"""
        try:
            # Get relevant staff users
            staff_users = User.objects.filter(is_staff=True, is_active=True)
            
            # Prepare notification data
            data = {
                'order_id': order.id,
                'order_number': order.order_number,
                'customer_name': order.customer_name,
                'total_amount': str(order.total_amount),
                'status': order.status,
                **(additional_data or {})
            }
            
            # Prepare title and message based on notification type
            if notification_type == 'order_received':
                title = f"📦 New Order #{order.order_number}"
                message = f"New order from {order.customer_name} for ${order.total_amount}"
            elif notification_type == 'order_started':
                title = f"👨‍🍳 Order #{order.order_number} Started"
                message = f"Order #{order.order_number} is now being prepared"
            elif notification_type == 'order_ready':
                title = f"✅ Order #{order.order_number} Ready"
                message = f"Order #{order.order_number} is ready for pickup/delivery"
            elif notification_type == 'order_completed':
                title = f"🎉 Order #{order.order_number} Completed"
                message = f"Order #{order.order_number} has been completed successfully"
            else:
                title = f"📋 Order #{order.order_number} Update"
                message = f"Order #{order.order_number} status: {order.status}"
            
            # Send to all staff users
            return self.send_bulk_notification(
                staff_users,
                notification_type,
                title,
                message,
                priority='high',
                data=data
            )
        
        except Exception as e:
            logger.error(f"Error sending order notification: {str(e)}")
            return False
    
    def send_station_alert(self, station, alert_type, message, priority='medium'):
        """Send station-related alerts"""
        try:
            # Get staff assigned to station
            staff_users = station.staff_assigned.all()
            
            if not staff_users.exists():
                # Send to all staff if no one is assigned
                staff_users = User.objects.filter(is_staff=True, is_active=True)
            
            data = {
                'station_id': station.id,
                'station_name': station.name,
                'station_type': station.station_type,
                'current_load': station.current_load,
                'capacity': station.capacity,
                'alert_type': alert_type
            }
            
            title = f"🍳 Station Alert: {station.name}"
            
            return self.send_bulk_notification(
                staff_users,
                'station_alert',
                title,
                message,
                priority=priority,
                data=data
            )
        
        except Exception as e:
            logger.error(f"Error sending station alert: {str(e)}")
            return False
    
    def send_inventory_alert(self, ingredient, current_stock, min_stock):
        """Send low inventory alerts"""
        try:
            # Get staff users with inventory management role
            staff_users = User.objects.filter(is_staff=True, is_active=True)
            
            data = {
                'ingredient_id': ingredient.id,
                'ingredient_name': ingredient.name,
                'current_stock': current_stock,
                'min_stock': min_stock,
                'unit': ingredient.unit,
                'supplier': ingredient.supplier
            }
            
            title = f"⚠️ Low Inventory: {ingredient.name}"
            message = f"{ingredient.name} is running low. Current: {current_stock} {ingredient.unit}, Min: {min_stock} {ingredient.unit}"
            
            return self.send_bulk_notification(
                staff_users,
                'low_inventory',
                title,
                message,
                priority='high',
                data=data,
                expires_minutes=120  # Keep for 2 hours
            )
        
        except Exception as e:
            logger.error(f"Error sending inventory alert: {str(e)}")
            return False
    
    def _get_user_preferences(self, user):
        """Get user notification preferences"""
        preference, created = NotificationPreference.objects.get_or_create(user=user)
        return preference
    
    def _should_send_notification(self, preferences, notification_type, priority):
        """Check if notification should be sent based on preferences"""
        # Check notification type preferences
        if notification_type in ['order_received', 'order_started', 'order_ready', 'order_completed']:
            if not preferences.order_notifications:
                return False
        elif notification_type == 'station_alert':
            if not preferences.station_alerts:
                return False
        elif notification_type == 'low_inventory':
            if not preferences.inventory_alerts:
                return False
        elif notification_type == 'system_alert':
            if not preferences.system_alerts:
                return False
        
        # Check priority level
        priority_levels = {'low': 1, 'medium': 2, 'high': 3, 'urgent': 4}
        min_priority_level = priority_levels.get(preferences.min_priority_level, 2)
        notification_priority = priority_levels.get(priority, 2)
        
        if notification_priority < min_priority_level:
            return False
        
        return True
    
    def _send_websocket_notification(self, recipient, notification):
        """Send notification via WebSocket"""
        try:
            channel_name = f"user_{recipient.id}"
            
            message = {
                'type': 'notification',
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'notification_type': notification.notification_type,
                'priority': notification.priority,
                'data': notification.data,
                'created_at': notification.created_at.isoformat(),
                'expires_at': notification.expires_at.isoformat() if notification.expires_at else None
            }
            
            async_to_sync(self.channel_layer.group_send)(
                channel_name,
                {
                    'type': 'notification_message',
                    'message': message
                }
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error sending WebSocket notification: {str(e)}")
            return False
    
    def _send_email_notification(self, recipient, notification):
        """Send notification via email (placeholder)"""
        # TODO: Implement email notification
        logger.info(f"Email notification would be sent to {recipient.email}: {notification.title}")
        return True
    
    def _send_sound_notification(self, recipient, notification):
        """Send sound notification (placeholder)"""
        # TODO: Implement sound notification
        logger.info(f"Sound notification would be played for {recipient.username}: {notification.title}")
        return True
    
    def create_notification_from_template(self, template_name, recipient, context):
        """Create notification from template"""
        try:
            template = NotificationTemplate.objects.get(name=template_name, is_active=True)
            
            title = template.render_title(context)
            message = template.render_message(context)
            
            return self.send_notification(
                recipient=recipient,
                notification_type=template.notification_type,
                title=title,
                message=message,
                priority=template.default_priority,
                expires_minutes=template.default_expires_minutes
            )
        
        except NotificationTemplate.DoesNotExist:
            logger.error(f"Notification template '{template_name}' not found")
            return False
        except Exception as e:
            logger.error(f"Error creating notification from template: {str(e)}")
            return False
    
    def mark_notification_read(self, notification_id, user):
        """Mark notification as read"""
        try:
            notification = Notification.objects.get(id=notification_id, recipient=user)
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False
    
    def get_unread_notifications(self, user, limit=50):
        """Get unread notifications for user"""
        return Notification.objects.filter(
            recipient=user,
            is_read=False
        ).exclude(
            expires_at__lt=timezone.now()
        ).order_by('-created_at')[:limit]
    
    def get_notification_by_id(self, notification_id, user):
        """Get a specific notification by ID for a user"""
        try:
            return Notification.objects.get(id=notification_id, recipient=user)
        except Notification.DoesNotExist:
            return None
    
    def cleanup_expired_notifications(self):
        """Clean up expired notifications"""
        expired_count = Notification.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()
        
        logger.info(f"Cleaned up {expired_count} expired notifications")
        return expired_count

# WebSocket Consumer for real-time notifications
class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time notifications"""
    
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_authenticated:
            self.room_group_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()
    
    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle incoming messages"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'mark_read':
                notification_id = text_data_json.get('notification_id')
                # Mark notification as read
                notification_service = NotificationService()
                success = notification_service.mark_notification_read(notification_id, self.user)
                
                await self.send(text_data=json.dumps({
                    'type': 'mark_read_response',
                    'success': success,
                    'notification_id': notification_id
                }))
            
            elif message_type == 'get_unread':
                notification_service = NotificationService()
                notifications = notification_service.get_unread_notifications(self.user)
                
                await self.send(text_data=json.dumps({
                    'type': 'unread_notifications',
                    'notifications': [
                        {
                            'id': n.id,
                            'title': n.title,
                            'message': n.message,
                            'notification_type': n.notification_type,
                            'priority': n.priority,
                            'created_at': n.created_at.isoformat(),
                            'data': n.data
                        }
                        for n in notifications
                    ]
                }))
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
