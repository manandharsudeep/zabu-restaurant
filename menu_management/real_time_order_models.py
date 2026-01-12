# -*- coding: utf-8 -*-
"""
Real-time Order Management Models
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import json
from decimal import Decimal

class RealTimeOrderTracking(models.Model):
    """Real-time order tracking and communication"""
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('picked_up', 'Picked Up'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    order = models.OneToOneField('order_orchestration.UnifiedOrderQueue', on_delete=models.CASCADE, related_name='real_time_tracking')
    
    # Real-time status
    current_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    status_updated_at = models.DateTimeField(auto_now=True)
    
    # Timing tracking
    prep_started_at = models.DateTimeField(null=True, blank=True)
    prep_completed_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Progress tracking
    progress_percentage = models.IntegerField(default=0)
    current_step = models.CharField(max_length=100, blank=True)
    estimated_completion = models.DateTimeField(null=True, blank=True)
    
    # Communication
    customer_notified = models.BooleanField(default=False)
    last_notification = models.DateTimeField(null=True, blank=True)
    notification_preferences = models.JSONField(default=dict)
    
    def __str__(self):
        return f"Tracking {self.order.order_id}"

class SpecialRequestManagement(models.Model):
    """Special request handling and communication to kitchen"""
    REQUEST_TYPES = [
        ('dietary', 'Dietary Restriction'),
        ('allergy', 'Allergy Alert'),
        ('modification', 'Order Modification'),
        ('timing', 'Timing Request'),
        ('packaging', 'Packaging Request'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('acknowledged', 'Acknowledged'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    
    request_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey('order_orchestration.UnifiedOrderQueue', on_delete=models.CASCADE, related_name='special_requests')
    
    # Request details
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    description = models.TextField()
    urgency = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='medium')
    
    # Status and handling
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_requests')
    
    # Communication
    kitchen_notified = models.BooleanField(default=False)
    customer_informed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Request {self.request_id} - {self.get_request_type_display()}"
