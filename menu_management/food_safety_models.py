from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json

class FoodSafetyLog(models.Model):
    """Automated food safety logging system"""
    LOG_TYPES = [
        ('temperature_check', 'Temperature Check'),
        ('sanitation_check', 'Sanitation Check'),
        ('equipment_check', 'Equipment Check'),
        ('pest_control', 'Pest Control'),
        ('food_preparation', 'Food Preparation'),
        ('storage_check', 'Storage Check'),
        ('delivery_inspection', 'Delivery Inspection'),
        ('allergen_control', 'Allergen Control'),
        ('staff_hygiene', 'Staff Hygiene'),
        ('waste_disposal', 'Waste Disposal'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('compliant', 'Compliant'),
        ('non_compliant', 'Non-Compliant'),
        ('corrective_action', 'Corrective Action Required'),
        ('resolved', 'Resolved'),
    ]
    
    log_type = models.CharField(max_length=20, choices=LOG_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='compliant')
    
    # Location and time
    location = models.CharField(max_length=100)  # Kitchen area, station, etc.
    station = models.CharField(max_length=100, blank=True)  # Specific station
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Measurement data
    temperature = models.FloatField(null=True, blank=True)  # Celsius
    target_temperature = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)  # Percentage
    
    # Description and notes
    description = models.TextField()
    notes = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    
    # Staff and verification
    logged_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='safety_logs')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_logs')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Automated flag
    is_automated = models.BooleanField(default=False)
    sensor_data = models.JSONField(default=dict)  # Raw sensor data
    
    # Compliance
    compliance_score = models.IntegerField(default=100)  # 0-100
    requires_follow_up = models.BooleanField(default=False)
    follow_up_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['log_type', 'timestamp']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['location', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_log_type_display()} - {self.location} - {self.timestamp}"
    
    def verify_log(self, user):
        """Verify the safety log"""
        self.verified_by = user
        self.verified_at = timezone.now()
        self.save()
    
    def mark_non_compliant(self, corrective_action_text):
        """Mark log as non-compliant and require corrective action"""
        self.status = 'non_compliant'
        self.corrective_action = corrective_action_text
        self.requires_follow_up = True
        self.follow_up_date = timezone.now() + timezone.timedelta(days=1)
        self.save()

class TemperatureLog(models.Model):
    """Detailed temperature logging with sensors"""
    SENSOR_TYPES = [
        ('probe', 'Probe Thermometer'),
        ('infrared', 'Infrared Thermometer'),
        ('ambient', 'Ambient Sensor'),
        ('refrigeration', 'Refrigeration Sensor'),
        ('freezer', 'Freezer Sensor'),
        ('cooking', 'Cooking Sensor'),
    ]
    
    sensor_type = models.CharField(max_length=20, choices=SENSOR_TYPES)
    sensor_id = models.CharField(max_length=100)  # Unique sensor identifier
    location = models.CharField(max_length=100)
    
    # Temperature readings
    current_temp = models.FloatField()  # Celsius
    target_temp = models.FloatField()
    min_safe_temp = models.FloatField()
    max_safe_temp = models.FloatField()
    
    # Time and context
    timestamp = models.DateTimeField(auto_now_add=True)
    food_item = models.CharField(max_length=100, blank=True)  # What's being measured
    measurement_context = models.CharField(max_length=100, blank=True)  # Cooking, cooling, holding, etc.
    
    # Status
    is_within_range = models.BooleanField()
    alert_triggered = models.BooleanField(default=False)
    alert_level = models.CharField(max_length=10, choices=FoodSafetyLog.PRIORITY_LEVELS, default='low')
    
    # Additional data
    humidity = models.FloatField(null=True, blank=True)
    battery_level = models.IntegerField(null=True, blank=True)  # For wireless sensors
    signal_strength = models.IntegerField(null=True, blank=True)  # For wireless sensors
    
    def __str__(self):
        return f"{self.location} - {self.current_temp}°C at {self.timestamp}"
    
    def check_temperature_range(self):
        """Check if temperature is within safe range"""
        self.is_within_range = self.min_safe_temp <= self.current_temp <= self.max_safe_temp
        
        # Determine alert level
        if not self.is_within_range:
            temp_diff = min(abs(self.current_temp - self.min_safe_temp), abs(self.current_temp - self.max_safe_temp))
            
            if temp_diff > 10:
                self.alert_level = 'critical'
            elif temp_diff > 5:
                self.alert_level = 'high'
            elif temp_diff > 2:
                self.alert_level = 'medium'
            else:
                self.alert_level = 'low'
            
            self.alert_triggered = True
        else:
            self.alert_triggered = False
            self.alert_level = 'low'
        
        self.save()

class HACCPLog(models.Model):
    """HACCP compliance logging"""
    CRITICAL_CONTROL_POINTS = [
        ('receiving', 'Receiving'),
        ('storage', 'Storage'),
        ('preparation', 'Preparation'),
        ('cooking', 'Cooking'),
        ('cooling', 'Cooling'),
        ('reheating', 'Reheating'),
        ('holding', 'Holding'),
        ('serving', 'Serving'),
        ('cleaning', 'Cleaning'),
        ('pest_control', 'Pest Control'),
    ]
    
    ccp = models.CharField(max_length=20, choices=CRITICAL_CONTROL_POINTS)
    location = models.CharField(max_length=100)
    
    # Monitoring data
    critical_limit = models.CharField(max_length=200)  # What the limit is
    actual_value = models.CharField(max_length=200)  # What was measured
    is_within_limit = models.BooleanField()
    
    # Time and verification
    timestamp = models.DateTimeField(auto_now_add=True)
    monitored_by = models.ForeignKey(User, on_delete=models.CASCADE)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Corrective actions
    requires_corrective_action = models.BooleanField(default=False)
    corrective_action_taken = models.TextField(blank=True)
    corrective_action_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='haccp_corrective_actions')
    corrective_action_at = models.DateTimeField(null=True, blank=True)
    
    # Documentation
    notes = models.TextField(blank=True)
    supporting_documents = models.JSONField(default=list)  # File paths or URLs
    
    def __str__(self):
        return f"HACCP {self.get_ccp_display()} - {self.location} - {self.timestamp}"

class SanitationLog(models.Model):
    """Sanitation and cleaning logs"""
    CLEANING_TYPES = [
        ('daily', 'Daily Cleaning'),
        ('weekly', 'Weekly Cleaning'),
        ('monthly', 'Monthly Cleaning'),
        ('deep_clean', 'Deep Clean'),
        ('equipment', 'Equipment Cleaning'),
        ('surface', 'Surface Sanitization'),
        ('floor', 'Floor Cleaning'),
        ('waste', 'Waste Management'),
    ]
    
    cleaning_type = models.CharField(max_length=20, choices=CLEANING_TYPES)
    area = models.CharField(max_length=100)
    equipment = models.CharField(max_length=100, blank=True)
    
    # Cleaning details
    cleaning_products = models.TextField(help_text="Products used")
    method = models.TextField(help_text="Cleaning method and procedure")
    duration_minutes = models.IntegerField()
    
    # Verification
    cleaned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sanitation_logs')
    inspected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='inspected_sanitation_logs')
    inspected_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    is_satisfactory = models.BooleanField(default=True)
    issues_found = models.TextField(blank=True)
    corrective_actions = models.TextField(blank=True)
    
    # Scheduling
    scheduled_time = models.DateTimeField()
    completed_at = models.DateTimeField(auto_now_add=True)
    next_due = models.DateTimeField()
    
    def __str__(self):
        return f"{self.get_cleaning_type_display()} - {self.area} - {self.completed_at}"

class EquipmentMaintenanceLog(models.Model):
    """Equipment maintenance and calibration logs"""
    maintenance_types = [
        ('calibration', 'Calibration'),
        ('cleaning', 'Cleaning'),
        ('repair', 'Repair'),
        ('inspection', 'Inspection'),
        ('replacement', 'Replacement'),
        ('upgrade', 'Upgrade'),
    ]
    
    equipment_name = models.CharField(max_length=100)
    equipment_id = models.CharField(max_length=100)
    maintenance_type = models.CharField(max_length=20, choices=maintenance_types)
    
    # Maintenance details
    description = models.TextField()
    parts_used = models.TextField(blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Timing and personnel
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    performed_at = models.DateTimeField()
    duration_minutes = models.IntegerField()
    
    # Results
    is_successful = models.BooleanField(default=True)
    issues_found = models.TextField(blank=True)
    next_maintenance_due = models.DateTimeField()
    
    # Documentation
    work_order_number = models.CharField(max_length=50, blank=True)
    technician_notes = models.TextField(blank=True)
    photos = models.JSONField(default=list)  # File paths
    
    def __str__(self):
        return f"{self.equipment_name} - {self.get_maintenance_type_display()} - {self.performed_at}"

class FoodSafetyAlert(models.Model):
    """Food safety alerts and notifications"""
    ALERT_TYPES = [
        ('temperature_violation', 'Temperature Violation'),
        ('sanitation_issue', 'Sanitation Issue'),
        ('equipment_failure', 'Equipment Failure'),
        ('pest_activity', 'Pest Activity'),
        ('allergen_contamination', 'Allergen Contamination'),
        ('expiry_alert', 'Expiry Alert'),
        ('recall', 'Product Recall'),
        ('inspection_finding', 'Inspection Finding'),
    ]
    
    alert_type = models.CharField(max_length=25, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=FoodSafetyLog.PRIORITY_LEVELS)
    
    # Alert details
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=100)
    
    # Status and resolution
    status = models.CharField(max_length=20, choices=FoodSafetyLog.STATUS_CHOICES, default='non_compliant')
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_by_date = models.DateTimeField(null=True, blank=True)
    
    # Related logs
    related_logs = models.ManyToManyField(FoodSafetyLog, blank=True)
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.title} - {self.created_at}"
    
    def resolve_alert(self, user, resolution_notes_text):
        """Resolve the alert"""
        self.is_resolved = True
        self.status = 'resolved'
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.resolution_notes = resolution_notes_text
        self.save()
