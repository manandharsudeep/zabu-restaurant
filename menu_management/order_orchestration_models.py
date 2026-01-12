# -*- coding: utf-8 -*-
"""
Order Orchestration Models - Unified Order Management
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import json
from decimal import Decimal

class UnifiedOrderQueue(models.Model):
    """Unified order queue across all platforms and brands"""
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('queued', 'Queued'),
        ('batched', 'Batched'),
        ('in_progress', 'In Progress'),
        ('ready', 'Ready'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
        ('vip', 'VIP'),
    ]
    
    order_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Source information
    source_type = models.CharField(max_length=20, choices=[
        ('pos', 'POS System'),
        ('delivery', 'Delivery Platform'),
        ('online', 'Online Ordering'),
        ('phone', 'Phone Order'),
        ('walkin', 'Walk-in'),
    ])
    source_id = models.CharField(max_length=100, blank=True)
    source_name = models.CharField(max_length=100, blank=True)
    
    # Brand and order details
    brand = models.ForeignKey('menu_management.VirtualBrand', on_delete=models.CASCADE, related_name='unified_orders')
    customer_name = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_type = models.CharField(max_length=20, choices=[
        ('regular', 'Regular'),
        ('vip', 'VIP'),
        ('new', 'New Customer'),
        ('repeat', 'Repeat Customer'),
    ], default='regular')
    
    # Order content
    items = models.JSONField(default=list)
    special_requests = models.TextField(blank=True)
    dietary_restrictions = models.TextField(blank=True)
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tip = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Timing
    order_time = models.DateTimeField(auto_now_add=True)
    promised_time = models.DateTimeField(null=True, blank=True)
    prep_time_estimate = models.IntegerField(default=15)  # minutes
    actual_prep_time = models.IntegerField(null=True, blank=True)
    
    # Status and priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # Batching
    batch_id = models.UUIDField(null=True, blank=True)
    batch_position = models.IntegerField(default=0)
    
    # Kitchen assignment
    assigned_station = models.CharField(max_length=100, blank=True)
    assigned_chef = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_orders')
    
    # Internal references
    kitchen_order = models.OneToOneField('menu_management.KitchenOrder', on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order {self.order_id} - {self.brand.name}"

class UnifiedOrderBatch(models.Model):
    """Order batching for kitchen efficiency"""
    batch_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Batch details
    brand = models.ForeignKey('menu_management.VirtualBrand', on_delete=models.CASCADE, related_name='order_batches')
    station = models.CharField(max_length=100)
    batch_type = models.CharField(max_length=20, choices=[
        ('prep', 'Preparation'),
        ('cooking', 'Cooking'),
        ('assembly', 'Assembly'),
        ('packaging', 'Packaging'),
    ], default='prep')
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Orders in batch
    orders = models.ManyToManyField(UnifiedOrderQueue, related_name='unified_batches')
    
    # Batch metrics
    total_items = models.IntegerField(default=0)
    total_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estimated_time = models.IntegerField(default=0)  # minutes
    actual_time = models.IntegerField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    
    def __str__(self):
        return f"Batch {self.batch_id} - {self.station}"

class OrderThrottling(models.Model):
    """Dynamic order throttling during peak times"""
    throttling_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Throttling rules
    brand = models.ForeignKey('menu_management.VirtualBrand', on_delete=models.CASCADE, related_name='throttling_rules')
    day_of_week = models.IntegerField(choices=[(i, str(i)) for i in range(7)])  # 0=Monday, 6=Sunday
    hour_start = models.TimeField()
    hour_end = models.TimeField()
    
    # Limits
    max_orders_per_hour = models.IntegerField(default=20)
    max_orders_per_15min = models.IntegerField(default=5)
    auto_reject_enabled = models.BooleanField(default=False)
    
    # Current status
    current_orders = models.IntegerField(default=0)
    current_rejections = models.IntegerField(default=0)
    last_reset = models.DateTimeField(auto_now_add=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Throttling {self.brand.name} - {self.day_of_week} {self.hour_start}-{self.hour_end}"

class CapacityManagement(models.Model):
    """Dynamic capacity management and forecasting"""
    capacity_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    brand = models.ForeignKey('menu_management.VirtualBrand', on_delete=models.CASCADE, related_name='capacity_management')
    date = models.DateField()
    
    # Capacity settings
    max_daily_orders = models.IntegerField(default=100)
    max_hourly_orders = models.IntegerField(default=20)
    current_orders = models.IntegerField(default=0)
    
    # Station capacities
    station_capacities = models.JSONField(default=dict)  # {"station_name": {"max": 10, "current": 5}}
    
    # Forecasting
    forecasted_orders = models.IntegerField(default=0)
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.50)
    
    # Performance metrics
    avg_prep_time = models.IntegerField(default=15)
    on_time_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.95)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Capacity {self.brand.name} - {self.date}"

class OrderPrioritization(models.Model):
    """Order prioritization algorithms"""
    RULE_TYPES = [
        ('first_in_first_out', 'First In, First Out'),
        ('delivery_time', 'Delivery Time Priority'),
        ('customer_tier', 'Customer Tier Priority'),
        ('order_value', 'Order Value Priority'),
        ('prep_time', 'Prep Time Priority'),
        ('dynamic', 'Dynamic Algorithm'),
    ]
    
    brand = models.ForeignKey('menu_management.VirtualBrand', on_delete=models.CASCADE, related_name='prioritization_rules')
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    
    # Rule parameters
    weight = models.DecimalField(max_digits=3, decimal_places=2, default=1.00)
    conditions = models.JSONField(default=dict)  # {"min_order_value": 50, "customer_tier": "vip"}
    
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)  # Higher number = higher priority
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.brand.name} - {self.get_rule_type_display()}"
