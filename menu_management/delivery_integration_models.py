# -*- coding: utf-8 -*-
"""
Delivery Platform Integration Models
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import json
from decimal import Decimal

class DeliveryPlatform(models.Model):
    """Delivery platform integration settings"""
    PLATFORMS = [
        ('uber_eats', 'Uber Eats'),
        ('doordash', 'DoorDash'),
        ('grubhub', 'Grubhub'),
        ('postmates', 'Postmates'),
        ('deliveroo', 'Deliveroo'),
        ('just_eat', 'Just Eat'),
        ('swiggy', 'Swiggy'),
        ('zomato', 'Zomato'),
        ('foodpanda', 'Foodpanda'),
        ('seamless', 'Seamless'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
        ('syncing', 'Syncing'),
        ('suspended', 'Suspended'),
    ]
    
    restaurant = models.ForeignKey('menu_management.VirtualBrand', on_delete=models.CASCADE, related_name='delivery_platforms')
    platform = models.CharField(max_length=20, choices=PLATFORMS)
    
    # API credentials
    client_id = models.CharField(max_length=255, blank=True)
    client_secret = models.CharField(max_length=255, blank=True)
    access_token = models.CharField(max_length=500, blank=True)
    refresh_token = models.CharField(max_length=500, blank=True)
    
    # Store/location info
    store_id = models.CharField(max_length=100, blank=True)
    store_name = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    
    # Platform settings
    is_active = models.BooleanField(default=True)
    auto_accept_orders = models.BooleanField(default=True)
    max_orders_per_hour = models.IntegerField(default=20)
    prep_time_minutes = models.IntegerField(default=15)
    
    # Pricing
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.30)
    delivery_fee = models.DecimalField(max_digits=5, decimal_places=2, default=2.99)
    minimum_order = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)
    
    # Sync settings
    auto_sync_menu = models.BooleanField(default=True)
    auto_sync_orders = models.BooleanField(default=True)
    sync_interval = models.IntegerField(default=300)  # seconds
    last_sync = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')
    
    # Webhook settings
    webhook_url = models.URLField(blank=True)
    webhook_secret = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['restaurant', 'platform']
    
    def __str__(self):
        return f"{self.restaurant.name} - {self.get_platform_display()}"

class DeliveryOrder(models.Model):
    """Orders from delivery platforms"""
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('accepted', 'Accepted'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('picked_up', 'Picked Up'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    ]
    
    platform = models.ForeignKey(DeliveryPlatform, on_delete=models.CASCADE, related_name='orders')
    platform_order_id = models.CharField(max_length=100)
    
    # Customer info
    customer_name = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_address = models.TextField(blank=True)
    delivery_instructions = models.TextField(blank=True)
    
    # Order details
    items = models.JSONField(default=list)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tip = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Timing
    order_time = models.DateTimeField()
    estimated_pickup = models.DateTimeField(null=True, blank=True)
    actual_pickup = models.DateTimeField(null=True, blank=True)
    delivery_time = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    rejection_reason = models.TextField(blank=True)
    
    # Driver info
    driver_name = models.CharField(max_length=100, blank=True)
    driver_phone = models.CharField(max_length=20, blank=True)
    driver_rating = models.IntegerField(null=True, blank=True)
    
    # Internal references
    kitchen_order = models.OneToOneField('menu_management.KitchenOrder', on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order {self.platform_order_id} from {self.platform.platform}"

class PlatformMenuSync(models.Model):
    """Menu synchronization tracking for delivery platforms"""
    platform = models.ForeignKey(DeliveryPlatform, on_delete=models.CASCADE, related_name='menu_syncs')
    
    sync_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sync_time = models.DateTimeField(auto_now_add=True)
    
    # Sync statistics
    items_added = models.IntegerField(default=0)
    items_updated = models.IntegerField(default=0)
    items_removed = models.IntegerField(default=0)
    items_total = models.IntegerField(default=0)
    
    # Sync details
    sync_details = models.JSONField(default=dict)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    def __str__(self):
        return f"Menu Sync {self.sync_id} - {self.platform.platform}"

class PlatformPerformance(models.Model):
    """Performance analytics for delivery platforms"""
    platform = models.ForeignKey(DeliveryPlatform, on_delete=models.CASCADE, related_name='performance')
    date = models.DateField()
    
    # Order metrics
    total_orders = models.IntegerField(default=0)
    completed_orders = models.IntegerField(default=0)
    cancelled_orders = models.IntegerField(default=0)
    rejected_orders = models.IntegerField(default=0)
    
    # Revenue metrics
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Performance metrics
    avg_prep_time = models.IntegerField(default=0)  # minutes
    avg_delivery_time = models.IntegerField(default=0)  # minutes
    on_time_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.platform.platform} - {self.date}"
