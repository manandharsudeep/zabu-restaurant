# -*- coding: utf-8 -*-
"""
Customer Service Tools Models
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import json
from decimal import Decimal

class VIPCustomerManagement(models.Model):
    """VIP customer identification and preferences"""
    TIER_CHOICES = [
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
        ('diamond', 'Diamond'),
    ]
    
    customer_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Customer identification
    phone_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)
    name = models.CharField(max_length=100)
    
    # VIP status
    tier = models.CharField(max_length=10, choices=TIER_CHOICES, default='bronze')
    total_orders = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Preferences
    preferred_items = models.JSONField(default=list)
    dietary_restrictions = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    
    # Benefits
    priority_support = models.BooleanField(default=False)
    exclusive_offers = models.BooleanField(default=False)
    personal_chef = models.BooleanField(default=False)
    
    # Communication preferences
    sms_notifications = models.BooleanField(default=True)
    email_updates = models.BooleanField(default=True)
    promotional_offers = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_tier_display()}"

class AllergyAlertProtocol(models.Model):
    """Allergy alert protocols"""
    PROTOCOL_STEPS = [
        ('alert_kitchen', 'Alert Kitchen'),
        ('separate_utensils', 'Use Separate Utensils'),
        ('dedicated_station', 'Use Dedicated Station'),
        ('manager_oversight', 'Manager Oversight'),
        ('customer_confirmation', 'Customer Confirmation'),
        ('final_check', 'Final Safety Check'),
    ]
    
    alert_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey('order_orchestration.UnifiedOrderQueue', on_delete=models.CASCADE, related_name='allergy_protocols')
    
    # Allergy details
    allergen = models.CharField(max_length=100)
    severity = models.CharField(max_length=20, choices=[
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('life_threatening', 'Life-Threatening'),
    ])
    
    # Protocol execution
    steps_completed = models.JSONField(default=list)
    current_step = models.CharField(max_length=50, blank=True)
    
    # Responsibility
    responsible_chef = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='allergy_protocols')
    manager_verified = models.BooleanField(default=False)
    
    # Documentation
    protocol_notes = models.TextField(blank=True)
    customer_informed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Allergy Protocol {self.alert_id} - {self.allergen}"

class CustomerFeedbackCollection(models.Model):
    """Customer feedback collection and analysis"""
    FEEDBACK_TYPES = [
        ('food_quality', 'Food Quality'),
        ('service', 'Service'),
        ('ambiance', 'Ambiance'),
        ('delivery', 'Delivery'),
        ('pricing', 'Pricing'),
        ('other', 'Other'),
    ]
    
    feedback_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey('order_orchestration.UnifiedOrderQueue', on_delete=models.CASCADE, related_name='feedback')
    
    # Customer information
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    
    # Feedback details
    rating = models.IntegerField(choices=[(i, f'{i} Stars') for i in range(1, 6)])
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES)
    comments = models.TextField()
    
    # Response management
    responded = models.BooleanField(default=False)
    response_text = models.TextField(blank=True)
    response_date = models.DateTimeField(null=True, blank=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback_responses')
    
    # Status
    is_resolved = models.BooleanField(default=False)
    priority = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], default='medium')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Feedback {self.feedback_id} - {self.rating} Stars"
