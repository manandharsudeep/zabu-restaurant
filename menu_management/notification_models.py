from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json

class Notification(models.Model):
    """Real-time notification system"""
    NOTIFICATION_TYPES = [
        ('order_received', 'Order Received'),
        ('order_started', 'Order Started'),
        ('order_ready', 'Order Ready'),
        ('order_completed', 'Order Completed'),
        ('station_alert', 'Station Alert'),
        ('low_inventory', 'Low Inventory'),
        ('equipment_issue', 'Equipment Issue'),
        ('staff_message', 'Staff Message'),
        ('system_alert', 'System Alert'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict)  # Additional notification data
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save()
    
    @property
    def is_expired(self):
        """Check if notification has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

class NotificationPreference(models.Model):
    """User notification preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Notification type preferences
    order_notifications = models.BooleanField(default=True)
    station_alerts = models.BooleanField(default=True)
    inventory_alerts = models.BooleanField(default=True)
    system_alerts = models.BooleanField(default=True)
    
    # Delivery preferences
    in_app_notifications = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=False)
    sound_notifications = models.BooleanField(default=True)
    
    # Priority filters
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    min_priority_level = models.CharField(
        max_length=10, 
        choices=PRIORITY_LEVELS, 
        default='medium'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} Preferences"

class NotificationChannel(models.Model):
    """Notification delivery channels"""
    CHANNEL_TYPES = [
        ('websocket', 'WebSocket'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPES)
    endpoint = models.CharField(max_length=255)  # Email, phone number, device token, etc.
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_channel_type_display()}"

class NotificationTemplate(models.Model):
    """Reusable notification templates"""
    name = models.CharField(max_length=100)
    notification_type = models.CharField(max_length=20, choices=Notification.NOTIFICATION_TYPES)
    title_template = models.CharField(max_length=200)
    message_template = models.TextField()
    
    # Default settings
    default_priority = models.CharField(max_length=10, choices=Notification.PRIORITY_LEVELS, default='medium')
    default_expires_minutes = models.IntegerField(default=60)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def render_title(self, context):
        """Render title template with context"""
        return self.title_template.format(**context)
    
    def render_message(self, context):
        """Render message template with context"""
        return self.message_template.format(**context)
