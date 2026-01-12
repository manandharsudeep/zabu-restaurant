from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json

class VirtualBrand(models.Model):
    """Virtual brand for cloud kitchen operations"""
    BRAND_TYPES = [
        ('fast_casual', 'Fast Casual'),
        ('fine_dining', 'Fine Dining'),
        ('cafe', 'Cafe'),
        ('bakery', 'Bakery'),
        ('pizza', 'Pizza'),
        ('asian', 'Asian Cuisine'),
        ('healthy', 'Healthy'),
        ('desserts', 'Desserts'),
    ]
    
    TARGET_MARKETS = [
        ('urban', 'Urban'),
        ('suburban', 'Suburban'),
        ('office', 'Office'),
        ('college', 'College'),
        ('family', 'Family'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    brand_type = models.CharField(max_length=20, choices=BRAND_TYPES)
    target_market = models.CharField(max_length=20, choices=TARGET_MARKETS, blank=True)
    logo = models.ImageField(upload_to='brand_logos/', blank=True)
    brand_color = models.CharField(max_length=7, default='#667eea')  # Hex color
    
    # Platform integration
    uber_eats_active = models.BooleanField(default=True)
    doordash_active = models.BooleanField(default=True)
    grubhub_active = models.BooleanField(default=False)
    
    # Pricing strategy
    base_markup = models.DecimalField(max_digits=5, decimal_places=2, default=300.00)  # Percentage
    delivery_fee = models.DecimalField(max_digits=5, decimal_places=2, default=2.99)
    min_order_amount = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)
    
    # Status and tracking
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name
    
    @property
    def total_menu_items(self):
        """Count total menu items across all menus"""
        from .models import Menu, RecipeMenuItem
        return RecipeMenuItem.objects.filter(menu_section__menu__brand=self).count()
    
    @property
    def total_revenue(self):
        """Calculate total revenue for this brand"""
        # This would be calculated from actual orders
        return 0.00  # Placeholder
    
    @property
    def shared_ingredients_count(self):
        """Count shared ingredients across brand menus"""
        # This would be calculated from actual ingredient usage
        return 0  # Placeholder
    
    @property
    def avg_order_value(self):
        """Calculate average order value"""
        # This would be calculated from actual orders
        return 0.00  # Placeholder

class PlatformIntegration(models.Model):
    """Platform integration settings and sync status"""
    PLATFORMS = [
        ('uber_eats', 'Uber Eats'),
        ('doordash', 'DoorDash'),
        ('grubhub', 'Grubhub'),
        ('postmates', 'Postmates'),
        ('seamless', 'Seamless'),
    ]
    
    brand = models.ForeignKey(VirtualBrand, on_delete=models.CASCADE)
    platform = models.CharField(max_length=20, choices=PLATFORMS)
    is_active = models.BooleanField(default=True)
    api_key = models.CharField(max_length=255, blank=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(max_length=20, default='pending')
    platform_menu_id = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.brand.name} - {self.get_platform_display()}"

class BrandPerformance(models.Model):
    """Performance analytics for virtual brands"""
    brand = models.ForeignKey(VirtualBrand, on_delete=models.CASCADE)
    date = models.DateField()
    total_orders = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    avg_order_value = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    top_items = models.JSONField(default=dict)  # Store top selling items
    customer_ratings = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    
    class Meta:
        unique_together = ['brand', 'date']
    
    def __str__(self):
        return f"{self.brand.name} - {self.date}"

class MenuOptimization(models.Model):
    """AI-powered menu optimization recommendations"""
    brand = models.ForeignKey(VirtualBrand, on_delete=models.CASCADE)
    recommendation_type = models.CharField(max_length=50)  # pricing, inventory, promotion, etc.
    priority = models.CharField(max_length=20, default='medium')  # low, medium, high
    title = models.CharField(max_length=200)
    description = models.TextField()
    expected_impact = models.CharField(max_length=100)  # revenue increase, cost reduction, etc.
    implementation_status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.brand.name} - {self.title}"

class SharedIngredient(models.Model):
    """Shared ingredients across virtual brands"""
    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE)
    brand = models.ForeignKey(VirtualBrand, on_delete=models.CASCADE)
    usage_frequency = models.IntegerField(default=0)  # How often used in recipes
    cost_optimization = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['ingredient', 'brand']
    
    def __str__(self):
        return f"{self.ingredient.name} - {self.brand.name}"

class GhostKitchenWorkflow(models.Model):
    """Ghost kitchen workflow optimization"""
    brand = models.ForeignKey(VirtualBrand, on_delete=models.CASCADE)
    station_name = models.CharField(max_length=100)  # prep, cooking, packaging, etc.
    avg_preparation_time = models.IntegerField(default=0)  # in minutes
    capacity_per_hour = models.IntegerField(default=0)
    efficiency_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    optimization_suggestions = models.JSONField(default=list)
    
    def __str__(self):
        return f"{self.brand.name} - {self.station_name}"
