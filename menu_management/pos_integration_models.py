# -*- coding: utf-8 -*-
"""
POS Integration Models and Views
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import json
from decimal import Decimal

class POSIntegration(models.Model):
    """POS system integration settings and management"""
    POS_SYSTEMS = [
        ('toast', 'Toast POS'),
        ('square', 'Square POS'),
        ('clover', 'Clover POS'),
        ('aloha', 'Aloha POS'),
        ('micros', 'Micros 3700'),
        ('revel', 'Revel Systems'),
        ('lightspeed', 'Lightspeed POS'),
        ('shopkeep', 'ShopKeep POS'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
        ('syncing', 'Syncing'),
    ]
    
    restaurant = models.ForeignKey('menu_management.VirtualBrand', on_delete=models.CASCADE, related_name='pos_integrations')
    pos_system = models.CharField(max_length=20, choices=POS_SYSTEMS)
    api_key = models.CharField(max_length=255, blank=True)
    api_secret = models.CharField(max_length=255, blank=True)
    location_id = models.CharField(max_length=100, blank=True)
    restaurant_id = models.CharField(max_length=100, blank=True)
    
    # Sync settings
    is_active = models.BooleanField(default=True)
    auto_sync = models.BooleanField(default=True)
    sync_interval = models.IntegerField(default=300)  # seconds
    last_sync = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')
    
    # Connection details
    api_endpoint = models.URLField(blank=True)
    webhook_url = models.URLField(blank=True)
    webhook_secret = models.CharField(max_length=100, blank=True)
    
    # Sync tracking
    orders_synced = models.IntegerField(default=0)
    menu_items_synced = models.IntegerField(default=0)
    last_order_sync = models.DateTimeField(null=True, blank=True)
    last_menu_sync = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['restaurant', 'pos_system']
    
    def __str__(self):
        return f"{self.restaurant.name} - {self.get_pos_system_display()}"

class POSOrder(models.Model):
    """Orders from POS systems"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    pos_integration = models.ForeignKey(POSIntegration, on_delete=models.CASCADE, related_name='orders')
    pos_order_id = models.CharField(max_length=100)
    pos_system = models.CharField(max_length=20)
    
    # Order details
    customer_name = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    table_number = models.CharField(max_length=10, blank=True)
    server_name = models.CharField(max_length=100, blank=True)
    
    # Order items (JSON field for flexibility)
    items = models.JSONField(default=list)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tip = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Payment
    payment_method = models.CharField(max_length=50, blank=True)
    payment_status = models.CharField(max_length=20, default='pending')
    
    # Status and timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    order_time = models.DateTimeField()
    ready_time = models.DateTimeField(null=True, blank=True)
    completed_time = models.DateTimeField(null=True, blank=True)
    
    # Internal references
    kitchen_order = models.OneToOneField('menu_management.KitchenOrder', on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order {self.pos_order_id} from {self.pos_system}"

class POSMenuSync(models.Model):
    """Menu synchronization tracking"""
    pos_integration = models.ForeignKey(POSIntegration, on_delete=models.CASCADE, related_name='menu_syncs')
    
    sync_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sync_time = models.DateTimeField(auto_now_add=True)
    items_added = models.IntegerField(default=0)
    items_updated = models.IntegerField(default=0)
    items_removed = models.IntegerField(default=0)
    items_total = models.IntegerField(default=0)
    
    sync_details = models.JSONField(default=dict)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    def __str__(self):
        return f"Menu Sync {self.sync_id} - {self.pos_integration.pos_system}"
