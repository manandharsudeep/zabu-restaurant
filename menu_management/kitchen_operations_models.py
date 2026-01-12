from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import uuid

# Import KitchenStation from routing_models
from .routing_models import KitchenStation

# 3.2.1 Order Management - Enhanced Models

class OrderSource(models.Model):
    """Order sources for integration"""
    SOURCE_TYPES = [
        ('pos', 'POS System'),
        ('online', 'Online Ordering'),
        ('delivery', 'Delivery Platform'),
        ('phone', 'Phone Order'),
        ('walkin', 'Walk-in'),
        ('kiosk', 'Self-service Kiosk'),
    ]
    
    name = models.CharField(max_length=100)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    api_endpoint = models.URLField(blank=True)
    api_key = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    integration_settings = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"

class KitchenOrder(models.Model):
    """Enhanced kitchen order with full management"""
    ORDER_TYPES = [
        ('dine_in', 'Dine In'),
        ('takeout', 'Takeout'),
        ('delivery', 'Delivery'),
        ('catering', 'Catering'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
        ('vip', 'VIP'),
    ]
    
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('cooking', 'Cooking'),
        ('plating', 'Plating'),
        ('quality_check', 'Quality Check'),
        ('ready', 'Ready'),
        ('served', 'Served'),
        ('cancelled', 'Cancelled'),
    ]
    
    order_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_order_id = models.CharField(max_length=100, blank=True)
    source = models.ForeignKey(OrderSource, on_delete=models.SET_NULL, null=True)
    
    # Order details
    order_type = models.CharField(max_length=20, choices=ORDER_TYPES)
    table_number = models.CharField(max_length=20, blank=True)
    customer_name = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    
    # Timing and priority
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    estimated_prep_time = models.IntegerField(help_text="Minutes")
    actual_prep_time = models.IntegerField(null=True, blank=True)
    
    # Special handling
    special_instructions = models.TextField(blank=True)
    dietary_restrictions = models.JSONField(default=list)
    allergen_alerts = models.JSONField(default=list)
    is_rush_order = models.BooleanField(default=False)
    is_vip_order = models.BooleanField(default=False)
    
    # Course management
    course_sequence = models.IntegerField(default=1)
    total_courses = models.IntegerField(default=1)
    parent_order = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='course_orders')
    
    # Timestamps
    received_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Staff
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_orders')
    expedited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='expedited_orders')
    
    def __str__(self):
        return f"Order {self.order_id} - {self.get_status_display()}"

class OrderItem(models.Model):
    """Individual items within an order"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('cooking', 'Cooking'),
        ('ready', 'Ready'),
        ('served', 'Served'),
        ('cancelled', 'Cancelled'),
    ]
    
    order = models.ForeignKey(KitchenOrder, on_delete=models.CASCADE, related_name='items')
    menu_item = models.CharField(max_length=200)
    quantity = models.IntegerField(default=1)
    modifications = models.JSONField(default=list)
    special_instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Station assignment
    assigned_station = models.ForeignKey(KitchenStation, on_delete=models.SET_NULL, null=True, blank=True)
    preparation_time = models.IntegerField(default=10)  # Minutes
    
    # Fire timing
    fire_time = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.quantity}x {self.menu_item} for Order {self.order.order_id}"

class KitchenDisplaySystem(models.Model):
    """KDS configuration and settings"""
    name = models.CharField(max_length=100)
    display_type = models.CharField(max_length=50)  # monitor, tablet, TV
    station_filter = models.JSONField(default=list)  # Which stations to show
    max_orders_displayed = models.IntegerField(default=20)
    auto_refresh_interval = models.IntegerField(default=5)  # Seconds
    show_completed_orders = models.BooleanField(default=True)
    completed_orders_timeout = models.IntegerField(default=30)  # Seconds
    
    # Layout settings
    layout_config = models.JSONField(default=dict)
    color_scheme = models.JSONField(default=dict)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"KDS - {self.name}"

# 3.2.3 Prep Management Models

class PrepItem(models.Model):
    """Items that require preparation"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100)
    
    # Preparation details
    prep_method = models.TextField()
    prep_time = models.IntegerField(help_text="Minutes")
    batch_size = models.IntegerField(default=1)
    yield_quantity = models.DecimalField(max_digits=10, decimal_places=3)
    yield_unit = models.CharField(max_length=50)
    
    # Storage and shelf life
    storage_requirements = models.TextField(blank=True)
    shelf_life_hours = models.IntegerField(default=24)
    par_level = models.DecimalField(max_digits=10, decimal_places=3)
    
    # Cost tracking
    ingredient_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class PrepTask(models.Model):
    """Preparation tasks with scheduling"""
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    task_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prep_item = models.ForeignKey(PrepItem, on_delete=models.CASCADE)
    
    # Scheduling
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Quantities
    target_quantity = models.DecimalField(max_digits=10, decimal_places=3)
    completed_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    waste_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    
    # Assignment
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_station = models.ForeignKey(KitchenStation, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    actual_duration = models.IntegerField(null=True, blank=True)  # Minutes
    
    # Quality control
    quality_notes = models.TextField(blank=True)
    yield_variance = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_prep_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Prep {self.prep_item.name} - {self.scheduled_date}"

class PrepChecklist(models.Model):
    """Mise en place checklists"""
    checklist_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    station = models.ForeignKey(KitchenStation, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    
    # Checklist items
    items = models.JSONField(default=list)  # List of checklist items with completion status
    
    # Timing
    checklist_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Assignment and completion
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_checklists')
    completed_at = models.DateTimeField(null=True, blank=True)
    
    is_completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.station.name} ({self.checklist_date})"

# 3.2.4 Cloud Kitchen Operations Models

class OrderBatch(models.Model):
    """Batched orders for cloud kitchen efficiency"""
    batch_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    
    # Batch criteria
    preparation_time = models.IntegerField(help_text="Similar prep time in minutes")
    cooking_method = models.CharField(max_length=100)
    packaging_type = models.CharField(max_length=100)
    
    # Orders in batch
    orders = models.ManyToManyField(KitchenOrder, related_name='order_batches')
    
    # Timing
    start_time = models.DateTimeField()
    completion_time = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, default='pending')
    priority = models.CharField(max_length=10, choices=KitchenOrder.PRIORITY_LEVELS, default='normal')
    
    # Efficiency metrics
    total_orders = models.IntegerField(default=0)
    efficiency_gain = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Percentage
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Batch {self.name} ({self.total_orders} orders)"

class AssemblyLine(models.Model):
    """Assembly line workflow for cloud kitchens"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Workflow steps
    steps = models.JSONField(default=list)  # Ordered list of workflow steps
    
    # Capacity and timing
    capacity_per_hour = models.IntegerField(default=50)
    avg_order_time = models.IntegerField(default=5)  # Minutes per order
    
    # Station assignments
    stations = models.ManyToManyField(KitchenStation, related_name='assembly_lines')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Assembly Line: {self.name}"

class PackagingStation(models.Model):
    """Packaging station workflow"""
    name = models.CharField(max_length=100)
    
    # Packaging types supported
    packaging_types = models.JSONField(default=list)
    
    # Quality control checkpoints
    quality_checkpoints = models.JSONField(default=list)
    
    # Staff assignment
    staff_assigned = models.ManyToManyField(User, blank=True)
    
    # Capacity
    capacity_per_hour = models.IntegerField(default=30)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Packaging: {self.name}"

class DriverHandoff(models.Model):
    """Driver coordination and handoff"""
    handoff_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Order information
    order = models.OneToOneField(KitchenOrder, on_delete=models.CASCADE)
    delivery_platform = models.CharField(max_length=100)
    driver_name = models.CharField(max_length=100)
    driver_phone = models.CharField(max_length=20)
    
    # Timing
    estimated_pickup = models.DateTimeField()
    actual_pickup = models.DateTimeField(null=True, blank=True)
    
    # Handoff details
    packaging_verified = models.BooleanField(default=False)
    temperature_verified = models.BooleanField(default=False)
    quality_verified = models.BooleanField(default=False)
    
    # Issues
    handoff_issues = models.TextField(blank=True)
    customer_notified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Handoff: {self.order.order_id} to {self.driver_name}"

# 3.2.5 Course Menu Coordination Models

class CourseMenu(models.Model):
    """Multi-course menu coordination"""
    menu_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    table_number = models.CharField(max_length=20)
    customer_count = models.IntegerField(default=1)
    
    # Course sequence
    courses = models.JSONField(default=list)  # Ordered list of courses
    current_course = models.IntegerField(default=0)
    
    # Timing
    start_time = models.DateTimeField(null=True, blank=True)
    estimated_duration = models.IntegerField(default=120)  # Minutes
    pacing_interval = models.IntegerField(default=15)  # Minutes between courses
    
    # Status
    status = models.CharField(max_length=20, default='active')
    
    # Staff
    server = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='served_menus')
    sommelier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sommelier_menus')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Course Menu: {self.table_number} - {self.name}"

class CourseTiming(models.Model):
    """Individual course timing coordination"""
    course_menu = models.ForeignKey(CourseMenu, on_delete=models.CASCADE, related_name='course_timings')
    course_number = models.IntegerField()
    course_name = models.CharField(max_length=200)
    
    # Timing
    scheduled_start = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    scheduled_completion = models.DateTimeField()
    actual_completion = models.DateTimeField(null=True, blank=True)
    
    # Kitchen coordination
    kitchen_station = models.ForeignKey(KitchenStation, on_delete=models.SET_NULL, null=True)
    plating_station = models.ForeignKey(KitchenStation, on_delete=models.SET_NULL, null=True, blank=True, related_name='plating_courses')
    
    # Status
    status = models.CharField(max_length=20, default='pending')
    
    # Special requirements
    dietary_accommodations = models.JSONField(default=list)
    special_plating = models.TextField(blank=True)
    
    def __str__(self):
        return f"Course {self.course_number}: {self.course_name}"

# 3.2.6 Enhanced Food Safety & Quality Control Models

class DigitalThermometer(models.Model):
    """Digital thermometer integration"""
    device_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    thermometer_type = models.CharField(max_length=50)  # probe, infrared, ambient
    
    # Calibration
    last_calibration = models.DateField()
    next_calibration = models.DateField()
    calibration_offset = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Integration
    api_endpoint = models.URLField(blank=True)
    is_connected = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Thermometer: {self.name} ({self.location})"

class KitchenTemperatureLog(models.Model):
    """Enhanced temperature logging with digital integration"""
    LOG_TYPES = [
        ('cooking', 'Cooking'),
        ('cooling', 'Cooling'),
        ('holding', 'Holding'),
        ('storage', 'Storage'),
        ('receiving', 'Receiving'),
        ('serving', 'Serving'),
    ]
    
    thermometer = models.ForeignKey(DigitalThermometer, on_delete=models.SET_NULL, null=True, blank=True)
    log_type = models.CharField(max_length=20, choices=LOG_TYPES)
    
    # Location and item
    location = models.CharField(max_length=100)
    food_item = models.CharField(max_length=200, blank=True)
    batch_number = models.CharField(max_length=100, blank=True)
    
    # Temperature readings
    current_temp = models.DecimalField(max_digits=5, decimal_places=2)
    target_temp = models.DecimalField(max_digits=5, decimal_places=2)
    min_safe_temp = models.DecimalField(max_digits=5, decimal_places=2)
    max_safe_temp = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Time and duration
    timestamp = models.DateTimeField(auto_now_add=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    
    # Status and alerts
    is_within_range = models.BooleanField(null=True, blank=True)
    alert_level = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='low')
    alert_triggered = models.BooleanField(default=False)
    
    # Staff
    logged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_temps')
    
    def __str__(self):
        return f"Temp Log: {self.food_item} - {self.current_temp}°C"

class SanitationChecklist(models.Model):
    """Sanitation checklists by area/equipment"""
    checklist_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    area = models.CharField(max_length=100)
    equipment = models.CharField(max_length=100, blank=True)
    
    # Checklist items
    items = models.JSONField(default=list)  # List of sanitation tasks
    
    # Timing
    checklist_date = models.DateField()
    checklist_type = models.CharField(max_length=50)  # opening, closing, deep_clean
    
    # Assignment and completion
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_sanitation')
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Verification
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_sanitation')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    is_completed = models.BooleanField(default=False)
    issues_found = models.JSONField(default=list)
    corrective_actions = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Sanitation: {self.area} - {self.checklist_date}"

class EquipmentMaintenance(models.Model):
    """Equipment maintenance logs and reminders"""
    equipment_id = models.CharField(max_length=100, unique=True)
    equipment_name = models.CharField(max_length=200)
    equipment_type = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    
    # Maintenance schedule
    maintenance_frequency = models.CharField(max_length=50)  # daily, weekly, monthly, quarterly
    last_maintenance = models.DateField()
    next_maintenance = models.DateField()
    
    # Maintenance details
    maintenance_tasks = models.JSONField(default=list)
    parts_required = models.JSONField(default=list)
    
    # Service provider
    service_provider = models.CharField(max_length=200, blank=True)
    contact_info = models.TextField(blank=True)
    
    # Status
    is_operational = models.BooleanField(default=True)
    issues_reported = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Equipment: {self.equipment_name}"

class HealthInspection(models.Model):
    """Health inspection preparation and tracking"""
    inspection_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inspection_date = models.DateField()
    inspector_name = models.CharField(max_length=200)
    inspection_agency = models.CharField(max_length=200)
    
    # Inspection type
    inspection_type = models.CharField(max_length=50)  # routine, follow_up, complaint
    
    # Preparation
    preparation_checklist = models.JSONField(default=list)
    preparation_completed = models.BooleanField(default=False)
    
    # Results
    inspection_result = models.CharField(max_length=20, blank=True)  # pass, fail, conditional
    score = models.IntegerField(null=True, blank=True)
    violations = models.JSONField(default=list)
    
    # Follow-up
    corrective_actions_required = models.JSONField(default=list)
    reinspection_date = models.DateField(null=True, blank=True)
    
    # Documentation
    report_file = models.FileField(upload_to='inspection_reports/', blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Inspection: {self.inspection_date} - {self.inspection_agency}"

class AllergenControl(models.Model):
    """Allergen cross-contamination prevention"""
    control_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    area = models.CharField(max_length=100)
    
    # Allergens present
    allergens_present = models.JSONField(default=list)  # List of allergens
    
    # Control measures
    control_measures = models.JSONField(default=list)
    cleaning_protocols = models.JSONField(default=list)
    
    # Staff training
    staff_trained = models.JSONField(default=list)  # List of trained staff
    last_training_date = models.DateField(null=True, blank=True)
    
    # Monitoring
    last_audit = models.DateField(null=True, blank=True)
    audit_results = models.JSONField(default=list)
    
    # Incidents
    incidents = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Allergen Control: {self.area}"

class FoodSafetyCertification(models.Model):
    """Food safety certification tracking for staff"""
    staff_member = models.ForeignKey(User, on_delete=models.CASCADE)
    certification_type = models.CharField(max_length=100)
    certification_number = models.CharField(max_length=100, blank=True)
    
    # Issuing organization
    issuing_organization = models.CharField(max_length=200)
    
    # Validity
    issue_date = models.DateField()
    expiry_date = models.DateField()
    is_current = models.BooleanField(default=True)
    
    # Training details
    training_hours = models.IntegerField(default=0)
    training_topics = models.JSONField(default=list)
    
    # Renewal
    renewal_required = models.BooleanField(default=False)
    renewal_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.staff_member.get_full_name()} - {self.certification_type}"
