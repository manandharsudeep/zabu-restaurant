from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class KitchenStation(models.Model):
    """Kitchen station with equipment and capabilities"""
    STATION_TYPES = [
        ('prep', 'Prep Station'),
        ('grill', 'Grill Station'),
        ('sauté', 'Sauté Station'),
        ('fry', 'Fry Station'),
        ('cold', 'Cold Prep Station'),
        ('pastry', 'Pastry Station'),
        ('packaging', 'Packaging Station'),
        ('expedite', 'Expedite Station'),
    ]
    
    name = models.CharField(max_length=100)
    station_type = models.CharField(max_length=20, choices=STATION_TYPES)
    capacity = models.IntegerField(default=5)  # Max concurrent orders
    current_load = models.IntegerField(default=0)  # Current orders
    efficiency_score = models.IntegerField(default=100)  # 0-100 efficiency
    avg_preparation_time = models.IntegerField(default=10)  # Minutes
    is_active = models.BooleanField(default=True)
    
    # Equipment and capabilities
    equipment = models.JSONField(default=list)  # List of equipment
    capabilities = models.JSONField(default=list)  # What it can prepare
    
    # Staff assignment
    staff_assigned = models.ManyToManyField(User, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_station_type_display()})"
    
    @property
    def load_percentage(self):
        if self.capacity <= 0:
            return 0
        return min(100, (self.current_load / self.capacity) * 100)
    
    @property
    def is_available(self):
        return self.current_load < self.capacity and self.is_active
    
    @property
    def staff_count(self):
        return self.staff_assigned.count()

class OrderRouting(models.Model):
    """Smart order routing to kitchen stations"""
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE)
    station = models.ForeignKey(KitchenStation, on_delete=models.CASCADE)
    routing_score = models.IntegerField(default=0)  # 0-100 routing preference
    estimated_time = models.IntegerField(default=0)  # Minutes
    priority = models.IntegerField(default=5)  # 1-10 priority level
    status = models.CharField(max_length=20, default='pending')  # pending, assigned, started, completed
    
    assigned_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order #{self.order.id} → {self.station.name}"
    
    @property
    def time_taken(self):
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds() / 60
        return 0

class RoutingRule(models.Model):
    """Rules for automatic order routing"""
    name = models.CharField(max_length=100)
    conditions = models.JSONField(default=dict)  # Routing conditions
    station_preferences = models.JSONField(default=list)  # Preferred stations
    priority = models.IntegerField(default=5)  # Rule priority
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class StationPerformance(models.Model):
    """Station performance tracking"""
    station = models.ForeignKey(KitchenStation, on_delete=models.CASCADE)
    date = models.DateField()
    
    orders_processed = models.IntegerField(default=0)
    avg_time_per_order = models.FloatField(default=0)
    accuracy_score = models.IntegerField(default=100)  # 0-100
    efficiency_score = models.IntegerField(default=100)  # 0-100
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.station.name} - {self.date}"
