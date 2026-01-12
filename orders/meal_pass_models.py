from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid

class MealPass(models.Model):
    """Meal pass subscription tiers"""
    TIER_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('super_special', 'Super Special'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField()  # 7, 30, 365
    meals_per_period = models.PositiveIntegerField(default=7)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    features = models.JSONField(default=dict)  # Store features as JSON
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_tier_display()})"
    
    class Meta:
        ordering = ['price', 'name']

class MealPassSubscription(models.Model):
    """User meal pass subscriptions"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('suspended', 'Suspended'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meal_pass = models.ForeignKey(MealPass, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    meals_remaining = models.PositiveIntegerField(default=0)
    total_meals = models.PositiveIntegerField(default=0)
    auto_renew = models.BooleanField(default=False)
    payment_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.meal_pass.name}"
    
    def is_valid(self):
        return self.status == 'active' and self.end_date > timezone.now() and self.meals_remaining > 0
    
    def use_meal(self):
        if self.is_valid():
            self.meals_remaining -= 1
            self.save()
            return True
        return False
    
    class Meta:
        ordering = ['-created_at']

class MealPassUsage(models.Model):
    """Track meal pass usage"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(MealPassSubscription, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, null=True, blank=True)
    amount_saved = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    used_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Meal usage by {self.user.username} at {self.used_at}"
    
    class Meta:
        ordering = ['-used_at']

class MealPassBenefit(models.Model):
    """Additional benefits for meal pass holders"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meal_pass = models.ForeignKey(MealPass, on_delete=models.CASCADE)
    benefit_type = models.CharField(max_length=50)  # discount, free_item, priority, etc.
    benefit_value = models.CharField(max_length=200)  # percentage, item name, etc.
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.meal_pass.name} - {self.benefit_type}"
    
    class Meta:
        ordering = ['meal_pass', 'benefit_type']
