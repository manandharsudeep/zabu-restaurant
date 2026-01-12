# -*- coding: utf-8 -*-
"""
Phase 3: Kitchen Layout Optimization and Packaging Management Models
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import json
from decimal import Decimal

class KitchenLayoutOptimization(models.Model):
    """Digital station maps and workflow diagrams"""
    layout_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Layout details
    brand = models.ForeignKey('menu_management.VirtualBrand', on_delete=models.CASCADE, related_name='kitchen_layouts')
    layout_name = models.CharField(max_length=100)
    layout_type = models.CharField(max_length=20, choices=[
        ('current', 'Current Layout'),
        ('proposed', 'Proposed Layout'),
        ('historical', 'Historical Layout'),
        ('simulation', 'Simulation Layout'),
    ], default='current')
    
    # Layout configuration
    dimensions = models.JSONField(default=dict)  # {"width": 20, "length": 15, "height": 10}  # in feet
    stations = models.JSONField(default=list)  # [{"id": "station1", "name": "Grill", "x": 5, "y": 3, "width": 4, "height": 3}]
    equipment = models.JSONField(default=list)  # [{"id": "equip1", "name": "Grill", "station": "station1", "x": 5.5, "y": 3.5}]
    
    # Workflow paths
    workflow_paths = models.JSONField(default=list)  # [{"from": "prep", "to": "grill", "path": [[5,3], [6,3], [7,3]]}]
    
    # Performance metrics
    efficiency_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    utilization_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    bottleneck_areas = models.JSONField(default=list)
    
    # Layout analysis
    total_distance = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # total workflow distance
    cross_traffic_areas = models.JSONField(default=list)
    dead_space_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Layout {self.layout_id} - {self.layout_name}"

class KitchenStationAssignment(models.Model):
    """Station assignment by brand and cuisine type"""
    assignment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Station details
    station_name = models.CharField(max_length=100)
    station_type = models.CharField(max_length=20, choices=[
        ('prep', 'Preparation'),
        ('cooking', 'Cooking'),
        ('assembly', 'Assembly'),
        ('packaging', 'Packaging'),
        ('cleaning', 'Cleaning'),
        ('storage', 'Storage'),
    ])
    
    # Brand and cuisine assignment
    brand = models.ForeignKey('menu_management.VirtualBrand', on_delete=models.CASCADE, related_name='station_assignments')
    cuisine_type = models.CharField(max_length=50, choices=[
        ('american', 'American'),
        ('italian', 'Italian'),
        ('asian', 'Asian'),
        ('mexican', 'Mexican'),
        ('indian', 'Indian'),
        ('mediterranean', 'Mediterranean'),
        ('fusion', 'Fusion'),
        ('other', 'Other'),
    ])
    
    # Capacity and equipment
    max_concurrent_orders = models.IntegerField(default=5)
    equipment_list = models.JSONField(default=list)  # ["grill", "fryer", "oven"]
    required_skills = models.JSONField(default=list)  # ["grill_master", "line_cook"]
    
    # Performance metrics
    avg_prep_time = models.IntegerField(default=15)  # minutes
    throughput_per_hour = models.IntegerField(default=20)
    quality_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Assignment rules
    priority_level = models.IntegerField(default=1)  # 1=low, 5=high
    auto_assignment_enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.station_name} - {self.brand.name}"

class HotColdZoneManagement(models.Model):
    """Hot/cold zone management"""
    zone_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Zone details
    zone_name = models.CharField(max_length=100)
    zone_type = models.CharField(max_length=10, choices=[
        ('hot', 'Hot Zone'),
        ('cold', 'Cold Zone'),
        ('dry', 'Dry Storage'),
        ('freezer', 'Freezer'),
        ('ambient', 'Ambient'),
    ])
    
    # Location and dimensions
    brand = models.ForeignKey('menu_management.VirtualBrand', on_delete=models.CASCADE, related_name='zones')
    location = models.CharField(max_length=100)
    dimensions = models.JSONField(default=dict)  # {"width": 10, "length": 8, "height": 8}
    
    # Temperature control
    target_temperature = models.DecimalField(max_digits=5, decimal_places=2)  # Celsius
    temperature_tolerance = models.DecimalField(max_digits=5, decimal_places=2, default=2.00)
    current_temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Storage capacity
    max_capacity = models.IntegerField(default=100)  # in kg or units
    current_capacity = models.IntegerField(default=0)
    utilization_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Zone rules
    allowed_items = models.JSONField(default=list)  # ["meat", "vegetables", "dairy"]
    prohibited_items = models.JSONField(default=list)  # ["raw_meat", "chemicals"]
    
    # Monitoring
    temperature_logs = models.JSONField(default=list)  # [{"time": "2024-01-01T10:00:00Z", "temp": 4.0}]
    last_inspection = models.DateTimeField(null=True, blank=True)
    compliance_status = models.CharField(max_length=20, choices=[
        ('compliant', 'Compliant'),
        ('warning', 'Warning'),
        ('non_compliant', 'Non-Compliant'),
    ], default='compliant')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.zone_name} - {self.get_zone_type_display()}"

class PickupAreaConfiguration(models.Model):
    """Pickup area configuration and optimization"""
    config_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Pickup area details
    brand = models.ForeignKey('menu_management.VirtualBrand', on_delete=models.CASCADE, related_name='pickup_areas')
    area_name = models.CharField(max_length=100)
    area_type = models.CharField(max_length=20, choices=[
        ('delivery', 'Delivery Pickup'),
        ('takeout', 'Takeout'),
        ('curbside', 'Curbside'),
        ('drive_thru', 'Drive-Thru'),
        ('in_store', 'In-Store'),
    ])
    
    # Location and layout
    location = models.CharField(max_length=100)
    coordinates = models.JSONField(default=dict)  # {"x": 0, "y": 0, "width": 10, "length": 5}
    
    # Capacity and flow
    max_concurrent_pickups = models.IntegerField(default=5)
    avg_pickup_time = models.IntegerField(default=3)  # minutes
    pickup_flow = models.JSONField(default=list)  # [{"step": "order_ready", "time": 0}, {"step": "customer_arrives", "time": 2}]
    
    # Staffing
    required_staff = models.IntegerField(default=1)
    staff_skills = models.JSONField(default=list)  # ["customer_service", "order_verification"]
    
    # Equipment
    equipment_list = models.JSONField(default=list)  # ["heating_lamp", "pickup_shelf", "signage"]
    
    # Performance metrics
    daily_pickups = models.IntegerField(default=0)
    avg_wait_time = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    customer_satisfaction = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.area_name} - {self.get_area_type_display()}"

class PackagingManagement(models.Model):
    """Brand-specific packaging inventory and tracking"""
    package_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Package details
    brand = models.ForeignKey('menu_management.VirtualBrand', on_delete=models.CASCADE, related_name='packaging')
    package_name = models.CharField(max_length=100)
    package_type = models.CharField(max_length=20, choices=[
        ('container', 'Container'),
        ('lid', 'Lid'),
        ('bag', 'Bag'),
        ('box', 'Box'),
        ('wrapping', 'Wrapping'),
        ('utensils', 'Utensils'),
        ('accessories', 'Accessories'),
    ])
    
    # Specifications
    dimensions = models.JSONField(default=dict)  # {"length": 10, "width": 8, "height": 4}  # in cm
    weight = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # in grams
    material = models.CharField(max_length=50, choices=[
        ('plastic', 'Plastic'),
        ('paper', 'Paper'),
        ('cardboard', 'Cardboard'),
        ('biodegradable', 'Biodegradable'),
        ('compostable', 'Compostable'),
        ('recycled', 'Recycled'),
    ])
    
    # Inventory
    current_stock = models.IntegerField(default=0)
    minimum_stock = models.IntegerField(default=50)
    maximum_stock = models.IntegerField(default=500)
    reorder_point = models.IntegerField(default=100)
    
    # Cost tracking
    unit_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    bulk_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    supplier = models.CharField(max_length=100, blank=True)
    
    # Usage tracking
    daily_usage = models.IntegerField(default=0)
    monthly_usage = models.IntegerField(default=0)
    usage_trend = models.JSONField(default=dict)  # {"2024-01": 1000, "2024-02": 1200}
    
    # Temperature requirements
    temperature_sensitive = models.BooleanField(default=False)
    storage_temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    temperature_logs = models.JSONField(default=list)
    
    # Sustainability
    eco_friendly = models.BooleanField(default=False)
    recyclable = models.BooleanField(default=False)
    compostable = models.BooleanField(default=False)
    carbon_footprint = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # kg CO2
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.package_name} - {self.brand.name}"

class PackagingCostTracking(models.Model):
    """Packaging cost tracking by brand and order"""
    tracking_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Order details
    brand = models.ForeignKey('menu_management.VirtualBrand', on_delete=models.CASCADE, related_name='packaging_costs')
    order_id = models.CharField(max_length=100)  # Reference to order
    order_date = models.DateField()
    
    # Packaging used
    packaging_items = models.JSONField(default=list)  # [{"package_id": "uuid", "quantity": 2, "cost": 1.50}]
    total_packaging_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Cost breakdown
    material_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    labor_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    disposal_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Optimization metrics
    cost_per_order = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    cost_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # of total order value
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Packaging Cost {self.tracking_id} - {self.brand.name}"

class TemperatureMonitoring(models.Model):
    """Temperature retention monitoring and testing"""
    monitoring_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Monitoring details
    brand = models.ForeignKey('menu_management.VirtualBrand', on_delete=models.CASCADE, related_name='temperature_monitoring')
    package_type = models.ForeignKey(PackagingManagement, on_delete=models.CASCADE, related_name='temperature_tests')
    
    # Test parameters
    test_date = models.DateTimeField()
    initial_temperature = models.DecimalField(max_digits=5, decimal_places=2)  # Celsius
    ambient_temperature = models.DecimalField(max_digits=5, decimal_places=2)  # Celsius
    test_duration = models.IntegerField(default=60)  # minutes
    
    # Temperature readings
    temperature_readings = models.JSONField(default=list)  # [{"time": 0, "temp": 70}, {"time": 30, "temp": 65}]
    final_temperature = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Performance metrics
    temperature_retention = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # percentage
    heat_loss_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # degrees per hour
    
    # Compliance
    meets_standards = models.BooleanField(default=False)
    safety_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # degrees above minimum
    
    # Test conditions
    food_type = models.CharField(max_length=50, choices=[
        ('hot_food', 'Hot Food'),
        ('cold_food', 'Cold Food'),
        ('frozen', 'Frozen'),
        ('ambient', 'Ambient'),
    ])
    food_volume = models.IntegerField(default=500)  # in grams
    
    tested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='temperature_tests')
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Temperature Test {self.monitoring_id} - {self.package_type.package_name}"
