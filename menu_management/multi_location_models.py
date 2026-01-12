# -*- coding: utf-8 -*-
"""
Phase 4: Multi-Location Cloud Kitchen Network and Hub-and-Spoke Operations
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import json
from decimal import Decimal

class CloudKitchenLocation(models.Model):
    """Individual cloud kitchen location"""
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('setup', 'Setup'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('closed', 'Closed'),
    ]
    
    KITCHEN_TYPES = [
        ('full_service', 'Full Service'),
        ('delivery_only', 'Delivery Only'),
        ('ghost_kitchen', 'Ghost Kitchen'),
        ('dark_kitchen', 'Dark Kitchen'),
        ('hybrid', 'Hybrid'),
    ]
    
    location_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic information
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)  # e.g., "LAX-01", "NYC-02"
    kitchen_type = models.CharField(max_length=20, choices=KITCHEN_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    
    # Location details
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=20)
    
    # Coordinates
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    
    # Contact information
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='managed_kitchens')
    
    # Capacity and operations
    max_daily_orders = models.IntegerField(default=500)
    max_concurrent_orders = models.IntegerField(default=50)
    operating_hours = models.JSONField(default=dict)  # {"monday": {"open": "08:00", "close": "22:00"}}
    
    # Brands and menus
    supported_brands = models.ManyToManyField('menu_management.VirtualBrand', related_name='kitchen_locations')
    brand_specific_menus = models.JSONField(default=dict)  # {"brand_id": {"menu_id": "uuid", "active": true}}
    
    # Equipment and facilities
    equipment_list = models.JSONField(default=list)  # ["grill", "fryer", "oven", "refrigerator"]
    facility_size = models.IntegerField(default=1000)  # square feet
    prep_stations = models.IntegerField(default=5)
    storage_areas = models.IntegerField(default=3)
    
    # Performance metrics
    avg_prep_time = models.IntegerField(default=15)  # minutes
    on_time_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.95)
    quality_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Financial
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    utility_costs = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    labor_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Status and timing
    is_active = models.BooleanField(default=False)
    opening_date = models.DateTimeField(null=True, blank=True)
    closing_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class LocationPerformanceMetrics(models.Model):
    """Location-specific performance metrics and comparison"""
    metrics_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    location = models.ForeignKey(CloudKitchenLocation, on_delete=models.CASCADE, related_name='performance_metrics')
    date = models.DateField()
    
    # Order metrics
    total_orders = models.IntegerField(default=0)
    completed_orders = models.IntegerField(default=0)
    cancelled_orders = models.IntegerField(default=0)
    late_orders = models.IntegerField(default=0)
    
    # Revenue metrics
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cost_per_order = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    profit_per_order = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Performance metrics
    avg_prep_time = models.IntegerField(default=0)  # minutes
    avg_delivery_time = models.IntegerField(default=0)  # minutes
    on_time_delivery_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    customer_satisfaction = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Efficiency metrics
    orders_per_hour = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    revenue_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    labor_efficiency = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Comparison metrics
    location_rank = models.IntegerField(default=0)  # rank among all locations
    percentile_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Metrics {self.metrics_id} - {self.location.name} - {self.date}"

class InterLocationInventoryTransfer(models.Model):
    """Inter-location inventory transfers"""
    transfer_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Transfer details
    source_location = models.ForeignKey(CloudKitchenLocation, on_delete=models.CASCADE, related_name='inventory_outgoing')
    destination_location = models.ForeignKey(CloudKitchenLocation, on_delete=models.CASCADE, related_name='inventory_incoming')
    
    # Item details
    item_name = models.CharField(max_length=100)
    item_category = models.CharField(max_length=50)
    quantity = models.IntegerField(default=0)
    unit = models.CharField(max_length=20, choices=[
        ('kg', 'Kilograms'),
        ('liters', 'Liters'),
        ('pieces', 'Pieces'),
        ('boxes', 'Boxes'),
        ('bags', 'Bags'),
    ])
    
    # Transfer information
    transfer_date = models.DateTimeField()
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='requested_transfers')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_transfers')
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('in_transit', 'In Transit'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='requested')
    
    # Logistics
    transport_method = models.CharField(max_length=20, choices=[
        ('internal', 'Internal Transport'),
        ('third_party', 'Third Party'),
        ('courier', 'Courier'),
        ('pickup', 'Customer Pickup'),
    ], default='internal')
    
    tracking_number = models.CharField(max_length=100, blank=True)
    estimated_arrival = models.DateTimeField(null=True, blank=True)
    actual_arrival = models.DateTimeField(null=True, blank=True)
    
    # Cost
    transfer_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    cost_center = models.CharField(max_length=50, default='inventory')
    
    # Quality control
    quality_checked = models.BooleanField(default=False)
    quality_notes = models.TextField(blank=True)
    temperature_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Transfer {self.transfer_id} - {self.source_location.name} to {self.destination_location.name}"

class StandardizedRecipe(models.Model):
    """Standardized recipes across locations with local variations"""
    recipe_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Recipe details
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    cuisine_type = models.CharField(max_length=50)
    
    # Standard recipe (base recipe)
    standard_ingredients = models.JSONField(default=dict)  # {"ingredient": {"quantity": 100, "unit": "g", "optional": false}}
    standard_instructions = models.TextField()
    standard_prep_time = models.IntegerField(default=15)  # minutes
    standard_yield = models.IntegerField(default=1)  # servings
    
    # Nutritional information
    calories_per_serving = models.IntegerField(default=0)
    protein = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    carbs = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    fat = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    
    # Cost information
    standard_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    cost_per_serving = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Quality standards
    quality_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    photo_url = models.URLField(blank=True)
    
    # Version control
    version = models.CharField(max_length=20, default='1.0')
    last_updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_recipes')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Recipe {self.recipe_id} - {self.name}"

class LocationRecipeVariation(models.Model):
    """Local variations of standardized recipes"""
    variation_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    recipe = models.ForeignKey(StandardizedRecipe, on_delete=models.CASCADE, related_name='variations')
    location = models.ForeignKey(CloudKitchenLocation, on_delete=models.CASCADE, related_name='recipe_variations')
    
    # Local variations
    ingredient_substitutions = models.JSONField(default=dict)  # {"original": "substitute", "ratio": 1.0}
    additional_ingredients = models.JSONField(default=list)  # [{"ingredient": "quantity", "unit"}]
    removed_ingredients = models.JSONField(default=list)  # ["ingredient1", "ingredient2"]
    
    # Local adjustments
    prep_time_adjustment = models.IntegerField(default=0)  # minutes
    yield_adjustment = models.IntegerField(default=0)  # servings
    instruction_modifications = models.TextField(blank=True)
    
    # Local costs
    local_cost_adjustment = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    local_cost_per_serving = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Local availability
    available_ingredients = models.JSONField(default=list)  # ["ingredient1", "ingredient2"]
    seasonal_substitutions = models.JSONField(default=dict)  # {"season": {"ingredient": "substitute"}}
    
    # Quality control
    local_quality_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    customer_feedback_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Variation {self.variation_id} - {self.recipe.name} at {self.location.name}"

class CentralPrepKitchen(models.Model):
    """Central prep kitchen to satellite finishing operations"""
    kitchen_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Kitchen details
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    kitchen_type = models.CharField(max_length=20, choices=[
        ('central_prep', 'Central Prep'),
        ('satellite_finishing', 'Satellite Finishing'),
        ('hybrid', 'Hybrid'),
    ])
    
    # Location
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    coordinates = models.JSONField(default=dict)  # {"lat": 34.0522, "lng": -118.2437}
    
    # Capacity
    max_daily_prep = models.IntegerField(default=1000)  # in kg or portions
    prep_stations = models.IntegerField(default=10)
    storage_capacity = models.IntegerField(default=5000)  # in kg
    
    # Satellite locations
    satellite_locations = models.ManyToManyField(CloudKitchenLocation, related_name='central_kitchens')
    service_radius = models.IntegerField(default=50)  # in km
    
    # Operations
    operating_hours = models.JSONField(default=dict)
    prep_schedule = models.JSONField(default=dict)  # {"day": {"items": ["item1", "item2"], "quantities": [100, 200]}}
    
    # Staffing
    staff_count = models.IntegerField(default=0)
    required_skills = models.JSONField(default=list)  # ["prep_cook", "food_safety"]
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Central Kitchen {self.kitchen_id} - {self.name}"

class BulkIngredientProcessing(models.Model):
    """Bulk ingredient processing and distribution scheduling"""
    processing_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Processing details
    central_kitchen = models.ForeignKey(CentralPrepKitchen, on_delete=models.CASCADE, related_name='processing_schedules')
    ingredient_name = models.CharField(max_length=100)
    processing_type = models.CharField(max_length=50, choices=[
        ('washing', 'Washing'),
        ('cutting', 'Cutting'),
        ('portioning', 'Portioning'),
        ('cooking', 'Cooking'),
        ('packaging', 'Packaging'),
        ('freezing', 'Freezing'),
    ])
    
    # Schedule
    processing_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    estimated_duration = models.IntegerField(default=60)  # minutes
    
    # Quantities
    input_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    output_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    yield_rate = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    
    # Distribution
    satellite_allocations = models.JSONField(default=dict)  # {"location_id": {"quantity": 100, "priority": "high"}}
    distribution_method = models.CharField(max_length=20, choices=[
        ('internal', 'Internal Transport'),
        ('third_party', 'Third Party'),
        ('pickup', 'Pickup'),
    ])
    
    # Quality control
    quality_standards = models.JSONField(default=dict)  # {"temperature": {"min": 4, "max": 8}}
    quality_checks = models.JSONField(default=list)  # [{"step": "visual", "passed": true}]
    
    # Cost
    processing_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    distribution_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='scheduled')
    
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='processed_ingredients')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Processing {self.processing_id} - {self.ingredient_name}"

class DistributedFinishingKitchen(models.Model):
    """Distributed finishing kitchen coordination"""
    kitchen_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Kitchen details
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    central_kitchen = models.ForeignKey(CentralPrepKitchen, on_delete=models.CASCADE, related_name='finishing_kitchens')
    
    # Location
    address = models.TextField()
    coordinates = models.JSONField(default=dict)
    
    # Capacity
    max_daily_orders = models.IntegerField(default=200)
    finishing_stations = models.IntegerField(default=5)
    holding_capacity = models.IntegerField(default=100)  # in portions
    
    # Operations
    supported_brands = models.ManyToManyField('menu_management.VirtualBrand', related_name='finishing_locations')
    finishing_capabilities = models.JSONField(default=list)  # ["heating", "assembly", "packaging"]
    
    # Staffing
    staff_count = models.IntegerField(default=0)
    required_skills = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Finishing Kitchen {self.kitchen_id} - {self.name}"

class InterLocationLogistics(models.Model):
    """Inter-location logistics and delivery scheduling"""
    logistics_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Route details
    route_name = models.CharField(max_length=100)
    central_kitchen = models.ForeignKey(CentralPrepKitchen, on_delete=models.CASCADE, related_name='logistics_routes')
    
    # Schedule
    departure_time = models.TimeField()
    estimated_duration = models.IntegerField(default=60)  # minutes
    frequency = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('twice_daily', 'Twice Daily'),
        ('weekly', 'Weekly'),
        ('on_demand', 'On Demand'),
    ])
    
    # Route stops
    stops = models.JSONField(default=list)  # [{"location_id": "uuid", "sequence": 1, "estimated_time": 15}]
    
    # Transportation
    vehicle_type = models.CharField(max_length=50, choices=[
        ('van', 'Van'),
        ('truck', 'Truck'),
        ('refrigerated_truck', 'Refrigerated Truck'),
        ('motorcycle', 'Motorcycle'),
    ])
    vehicle_capacity = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # in kg
    driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='driven_routes')
    
    # Cost
    fuel_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    labor_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    maintenance_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Performance
    on_time_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    delivery_success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    customer_satisfaction = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Logistics {self.logistics_id} - {self.route_name}"
