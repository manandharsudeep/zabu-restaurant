# -*- coding: utf-8 -*-
"""
Advanced Scheduling Features - Labor Optimization and Compliance
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import json
from decimal import Decimal

class LaborLawCompliance(models.Model):
    """Labor law compliance tracking"""
    COMPLIANCE_TYPES = [
        ('break_duration', 'Break Duration'),
        ('overtime_hours', 'Overtime Hours'),
        ('minor_restrictions', 'Minor Restrictions'),
        ('rest_periods', 'Rest Periods'),
        ('maximum_hours', 'Maximum Hours'),
        ('day_off_requirements', 'Day Off Requirements'),
    ]
    
    JURISDICTIONS = [
        ('federal', 'Federal'),
        ('state', 'State'),
        ('local', 'Local'),
        ('union', 'Union Contract'),
    ]
    
    compliance_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Compliance details
    compliance_type = models.CharField(max_length=20, choices=COMPLIANCE_TYPES)
    jurisdiction = models.CharField(max_length=20, choices=JURISDICTIONS)
    rule_description = models.TextField()
    
    # Requirements
    minimum_break_minutes = models.IntegerField(default=30)
    maximum_daily_hours = models.IntegerField(default=8)
    maximum_weekly_hours = models.IntegerField(default=40)
    overtime_threshold = models.IntegerField(default=8)
    
    # Age restrictions
    minimum_age = models.IntegerField(default=16)
    minor_max_hours = models.IntegerField(default=6)
    minor_late_hours = models.BooleanField(default=True)
    
    # Enforcement
    is_active = models.BooleanField(default=True)
    penalty_description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_compliance_type_display()} - {self.get_jurisdiction_display()}"

class ScheduleOptimization(models.Model):
    """Schedule optimization for labor cost control"""
    OPTIMIZATION_TYPES = [
        ('cost_minimization', 'Cost Minimization'),
        ('coverage_optimization', 'Coverage Optimization'),
        ('skill_matching', 'Skill Matching'),
        ('peak_efficiency', 'Peak Efficiency'),
        ('employee_satisfaction', 'Employee Satisfaction'),
    ]
    
    optimization_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Optimization parameters
    optimization_type = models.CharField(max_length=20, choices=OPTIMIZATION_TYPES)
    target_date = models.DateField()
    brand = models.ForeignKey('menu_management.VirtualBrand', on_delete=models.CASCADE, related_name='schedule_optimizations')
    
    # Cost parameters
    target_labor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_labor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_savings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Coverage requirements
    required_positions = models.JSONField(default=dict)  # {"position": {"min": 2, "max": 4}}
    skill_requirements = models.JSONField(default=dict)  # {"position": ["skill1", "skill2"]}
    
    # Optimization results
    optimized_schedule = models.JSONField(default=dict)
    efficiency_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    compliance_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Status
    applied = models.BooleanField(default=False)
    results_tracked = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Optimization {self.optimization_id} - {self.get_optimization_type_display()}"

class ForecastedLaborRequirements(models.Model):
    """Forecasted labor requirement calculation"""
    forecast_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Forecast details
    brand = models.ForeignKey('menu_management.VirtualBrand', on_delete=models.CASCADE, related_name='labor_forecasts')
    forecast_date = models.DateField()
    forecast_type = models.CharField(max_length=20, choices=[
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ], default='hourly')
    
    # Input data
    expected_orders = models.IntegerField(default=0)
    expected_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    weather_factor = models.DecimalField(max_digits=3, decimal_places=2, default=1.00)
    event_factor = models.DecimalField(max_digits=3, decimal_places=2, default=1.00)
    
    # Forecast results
    required_staff = models.IntegerField(default=0)
    required_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    estimated_labor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Confidence metrics
    confidence_level = models.DecimalField(max_digits=3, decimal_places=2, default=0.80)
    historical_accuracy = models.DecimalField(max_digits=3, decimal_places=2, default=0.85)
    
    # Breakdown by position
    position_requirements = models.JSONField(default=dict)  # {"position": {"count": 2, "hours": 8}}
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Forecast {self.forecast_id} - {self.forecast_date}"

class MultiLocationScheduling(models.Model):
    """Multi-location scheduling for floating staff"""
    schedule_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Staff and locations
    staff = models.ForeignKey('staff_management.StaffProfile', on_delete=models.CASCADE, related_name='multi_location_schedules')
    primary_location = models.CharField(max_length=100)
    secondary_locations = models.JSONField(default=list)  # ["location1", "location2"]
    
    # Schedule details
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Location assignments
    location_assignments = models.JSONField(default=dict)  # {"time": "location"}
    travel_time = models.IntegerField(default=0)  # minutes between locations
    
    # Compensation
    base_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    travel_allowance = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    location_differential = models.JSONField(default=dict)  # {"location": "rate_multiplier"}
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ], default='draft')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Multi-Location {self.schedule_id} - {self.staff.user.get_full_name()}"

class SkillBasedScheduling(models.Model):
    """Skill-based scheduling with certifications and training levels"""
    SKILL_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
        ('master', 'Master'),
    ]
    
    schedule_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Skill requirements
    position = models.CharField(max_length=100)
    required_skills = models.JSONField(default=list)  # ["skill1", "skill2"]
    minimum_level = models.CharField(max_length=20, choices=SKILL_LEVELS, default='intermediate')
    
    # Staff assignment
    assigned_staff = models.ForeignKey('staff_management.StaffProfile', on_delete=models.CASCADE, related_name='skill_based_schedules')
    
    # Skill verification
    staff_skills = models.JSONField(default=dict)  # {"skill": {"level": "advanced", "certified": True}}
    skill_match_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Schedule details
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Training requirements
    training_required = models.BooleanField(default=False)
    training_assigned = models.BooleanField(default=False)
    training_completed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Skill Schedule {self.schedule_id} - {self.position}"

class PeakPeriodSurgeStaffing(models.Model):
    """Peak period surge staffing management"""
    surge_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Surge details
    brand = models.ForeignKey('menu_management.VirtualBrand', on_delete=models.CASCADE, related_name='surge_staffing')
    surge_type = models.CharField(max_length=20, choices=[
        ('lunch_rush', 'Lunch Rush'),
        ('dinner_rush', 'Dinner Rush'),
        ('weekend', 'Weekend'),
        ('holiday', 'Holiday'),
        ('event', 'Special Event'),
        ('weather', 'Weather Related'),
    ])
    
    # Timing
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_hours = models.IntegerField(default=0)
    
    # Staffing requirements
    base_staff_count = models.IntegerField(default=0)
    surge_multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=1.5)
    total_staff_needed = models.IntegerField(default=0)
    
    # Staff pool
    available_staff = models.ManyToManyField('staff_management.StaffProfile', related_name='surge_assignments')
    assigned_staff = models.ManyToManyField('staff_management.StaffProfile', related_name='surge_schedules', blank=True)
    
    # Compensation
    surge_rate_multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=1.5)
    bonus_per_hour = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Status
    activated = models.BooleanField(default=False)
    staff_notified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Surge {self.surge_id} - {self.get_surge_type_display()}"
