from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from decimal import Decimal

# Import additional models
from .inventory_models import *
from .staff_models import *
from .kitchen_operations_models import *

# Food Safety Models
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
    monitored_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='haccp_monitored_logs')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='haccp_verified_logs')
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

# Original models continue below...

class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=50)  # kg, g, l, ml, pcs, etc.
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    supplier = models.CharField(max_length=100, blank=True)
    allergen_info = models.TextField(blank=True)
    nutritional_info = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.unit})"

class Recipe(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    instructions = models.TextField()
    prep_time = models.IntegerField(help_text="Minutes")
    cook_time = models.IntegerField(help_text="Minutes")
    total_time = models.IntegerField(help_text="Minutes")
    difficulty = models.IntegerField(choices=[(1, 'Easy'), (2, 'Medium'), (3, 'Hard')], default=1)
    portions = models.IntegerField(default=1)
    cost_per_portion = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    chef_notes = models.TextField(blank=True)
    equipment_needed = models.TextField(blank=True)
    temperature_specs = models.TextField(blank=True)
    nutritional_info = models.JSONField(default=dict)
    allergen_info = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredients')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit = models.CharField(max_length=50)
    optional = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.quantity} {self.unit} {self.ingredient.name}"

class RecipeVersion(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField()
    name = models.CharField(max_length=200)
    changes_made = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_current = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.recipe.name} v{self.version_number}"

class RecipeMenuItemLink(models.Model):
    """Automatic linking between recipes and menu items across the system"""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='menu_item_links')
    menu_item = models.ForeignKey('orders.MenuItem', on_delete=models.CASCADE, related_name='recipe_links')
    is_primary_recipe = models.BooleanField(default=True)  # Primary recipe for this menu item
    auto_created = models.BooleanField(default=True)  # Auto-linked vs manual
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ['recipe', 'menu_item']
        verbose_name = "Recipe-Menu Item Link"
    
    def __str__(self):
        return f"{self.recipe.name} ↔ {self.menu_item.name}"

# Multi-Brand Management Models
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
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
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

class Menu(models.Model):
    """Menu with sections and items"""
    MENU_TYPES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('bar', 'Bar'),
        ('dessert', 'Dessert'),
        ('catering', 'Catering'),
        ('seasonal', 'Seasonal'),
        ('tasting', 'Tasting Menu'),
    ]
    
    name = models.CharField(max_length=100)
    menu_type = models.CharField(max_length=20, choices=MENU_TYPES)
    description = models.TextField(blank=True)
    # brand = models.ForeignKey(VirtualBrand, on_delete=models.CASCADE, null=True, blank=True)  # Temporarily commented
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.name} ({self.menu_type})"

class Course(models.Model):
    COURSE_TYPES = [
        ('appetizer', 'Appetizer'),
        ('soup', 'Soup'),
        ('salad', 'Salad'),
        ('main', 'Main Course'),
        ('dessert', 'Dessert'),
        ('beverage', 'Beverage'),
    ]
    
    name = models.CharField(max_length=100)
    course_type = models.CharField(max_length=20, choices=COURSE_TYPES)
    order = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name

class MenuSection(models.Model):
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.menu.name} - {self.name}"

class RecipeMenuItem(models.Model):
    menu_section = models.ForeignKey(MenuSection, on_delete=models.CASCADE, related_name='items')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    dietary_info = models.JSONField(default=dict)  # vegetarian, vegan, gluten-free, etc.
    prep_time = models.IntegerField(blank=True, null=True)
    plating_instructions = models.TextField(blank=True)
    chef_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class MenuPricing(models.Model):
    menu_item = models.ForeignKey(RecipeMenuItem, on_delete=models.CASCADE, related_name='pricing')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    markup_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    
    def calculate_markup(self):
        if self.cost > 0:
            return ((self.price - self.cost) / self.cost) * 100
        return 0
    
    def __str__(self):
        return f"{self.menu_item.name} - ${self.price}"

class MenuAvailability(models.Model):
    menu_item = models.ForeignKey(RecipeMenuItem, on_delete=models.CASCADE, related_name='availability')
    day_of_week = models.IntegerField(choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')])
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.menu_item.name} - {self.get_day_of_week_display()}"

class MenuAnalytics(models.Model):
    menu_item = models.ForeignKey(RecipeMenuItem, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    orders_count = models.IntegerField(default=0)
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    views = models.IntegerField(default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.menu_item.name} - {self.date}"


# Multi-Brand Management Models
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
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
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

class Station(models.Model):
    """Kitchen station for workflow management"""
    STATION_TYPES = [
        ('prep', 'Preparation'),
        ('cooking', 'Cooking'),
        ('packaging', 'Packaging'),
        ('cleaning', 'Cleaning'),
        ('quality_control', 'Quality Control'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    station_type = models.CharField(max_length=20, choices=STATION_TYPES, default='prep')
    capacity = models.IntegerField(default=5)
    current_orders = models.IntegerField(default=0)
    max_orders = models.IntegerField(default=10)
    equipment = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name
    
    @property
    def utilization_rate(self):
        """Calculate station utilization rate"""
        if self.max_orders > 0:
            return (self.current_orders / self.max_orders) * 100
        return 0
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class ABTest(models.Model):
    """A/B Testing for menu items"""
    TEST_TYPES = [
        ('price', 'Price Test'),
        ('description', 'Description Test'),
        ('image', 'Image Test'),
        ('position', 'Position Test'),
        ('bundle', 'Bundle Test'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    test_type = models.CharField(max_length=20, choices=TEST_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Test configuration
    control_group_size = models.IntegerField(default=50)  # percentage
    test_group_size = models.IntegerField(default=50)     # percentage
    confidence_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=95.00)
    
    # Test timing
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    duration_days = models.IntegerField(default=7)
    
    # Results
    control_conversions = models.IntegerField(default=0)
    test_conversions = models.IntegerField(default=0)
    control_views = models.IntegerField(default=0)
    test_views = models.IntegerField(default=0)
    
    # Statistical results
    significance = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    confidence_interval = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    winner = models.CharField(max_length=20, null=True, blank=True)  # 'control', 'test', 'inconclusive'
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.name} - {self.get_test_type_display()}"
    
    @property
    def conversion_rate_control(self):
        if self.control_views > 0:
            return (self.control_conversions / self.control_views) * 100
        return 0
    
    @property
    def conversion_rate_test(self):
        if self.test_views > 0:
            return (self.test_conversions / self.test_views) * 100
        return 0
    
    @property
    def is_active(self):
        if self.status == 'running' and self.start_date and self.end_date:
            now = timezone.now()
            return self.start_date <= now <= self.end_date
        return False

class ABTestVariant(models.Model):
    """A/B Test variants (control and test versions)"""
    test = models.ForeignKey(ABTest, on_delete=models.CASCADE, related_name='variants')
    variant_type = models.CharField(max_length=10)  # 'control' or 'test'
    menu_item = models.ForeignKey('RecipeMenuItem', on_delete=models.CASCADE, null=True, blank=True)
    
    # Variant data (JSON field for flexibility)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    position = models.IntegerField(default=0)
    
    # Performance metrics
    views = models.IntegerField(default=0)
    clicks = models.IntegerField(default=0)
    conversions = models.IntegerField(default=0)
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.test.name} - {self.variant_type}"
    
    @property
    def conversion_rate(self):
        if self.views > 0:
            return (self.conversions / self.views) * 100
        return 0

class MenuOptimization(models.Model):
    """AI-powered menu optimization suggestions"""
    OPTIMIZATION_TYPES = [
        ('pricing', 'Pricing Optimization'),
        ('placement', 'Menu Placement'),
        ('bundle', 'Bundle Suggestion'),
        ('promotion', 'Promotion Strategy'),
        ('inventory', 'Inventory Optimization'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low Priority'),
        ('medium', 'Medium Priority'),
        ('high', 'High Priority'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewing', 'Reviewing'),
        ('implemented', 'Implemented'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    optimization_type = models.CharField(max_length=20, choices=OPTIMIZATION_TYPES, default='pricing')
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Target items
    # menu_items = models.ManyToManyField('RecipeMenuItem', blank=True, related_name='optimizations')
    brand = models.ForeignKey('VirtualBrand', on_delete=models.CASCADE, null=True, blank=True)
    
    # Expected impact
    expected_revenue_increase = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # percentage
    expected_cost_reduction = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)     # percentage
    expected_order_increase = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)     # percentage
    
    # AI confidence and reasoning
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # 0-100
    ai_reasoning = models.TextField(blank=True)
    data_points_analyzed = models.IntegerField(default=0)
    
    # Implementation details
    implementation_steps = models.TextField(blank=True)
    required_resources = models.TextField(blank=True)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_time = models.IntegerField(null=True, blank=True)  # days
    
    # Results tracking
    actual_revenue_impact = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost_impact = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    implementation_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    
    def __str__(self):
        return f"{self.title} - {self.get_optimization_type_display()}"
    
    @property
    def is_implemented(self):
        return self.status == 'implemented' or self.status == 'completed'
    
    @property
    def roi(self):
        if self.estimated_cost and self.actual_revenue_impact:
            return ((self.actual_revenue_impact - self.estimated_cost) / self.estimated_cost) * 100
        return 0

class AnalyticsDashboard(models.Model):
    """Analytics dashboard configuration and data"""
    DASHBOARD_TYPES = [
        ('overview', 'Overview Dashboard'),
        ('sales', 'Sales Analytics'),
        ('menu', 'Menu Performance'),
        ('customer', 'Customer Behavior'),
        ('operational', 'Operational Metrics'),
    ]
    
    name = models.CharField(max_length=100)
    dashboard_type = models.CharField(max_length=20, choices=DASHBOARD_TYPES)
    configuration = models.JSONField(default=dict)  # Store dashboard layout and widgets
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.name} - {self.get_dashboard_type_display()}"

# Missing Models for Complete System Functionality
# Only adding models that don't already exist in other files

class StationAssignment(models.Model):
    """Staff assignments to kitchen stations"""
    station = models.ForeignKey('Station', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50)  # Grill Chef, Prep Cook, etc.
    assigned_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.station.name} ({self.role})"

class BrandInventoryAllocation(models.Model):
    """Inventory allocation for virtual brands"""
    brand = models.ForeignKey('VirtualBrand', on_delete=models.CASCADE)
    item = models.ForeignKey('InventoryItem', on_delete=models.CASCADE)
    allocated_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
    allocation_date = models.DateField()
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.brand.name} - {self.item.name} ({self.allocated_quantity} {self.unit})"

class CostAnalysis(models.Model):
    """Food cost and profitability analysis"""
    analysis_date = models.DateField()
    theoretical_food_cost = models.DecimalField(max_digits=5, decimal_places=2)  # Percentage
    actual_food_cost = models.DecimalField(max_digits=5, decimal_places=2)  # Percentage
    variance_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    total_sales = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    waste_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    menu_category = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Cost Analysis - {self.analysis_date} ({self.actual_food_cost}%)"

class WasteTracking(models.Model):
    """Track food waste for cost control"""
    item = models.ForeignKey('InventoryItem', on_delete=models.CASCADE)
    waste_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
    waste_type = models.CharField(max_length=50, choices=[
        ('spoilage', 'Spoilage'),
        ('over_production', 'Over Production'),
        ('prep_waste', 'Prep Waste'),
        ('customer_return', 'Customer Return'),
        ('theft', 'Theft'),
        ('other', 'Other')
    ])
    reason = models.CharField(max_length=200)
    cost_value = models.DecimalField(max_digits=8, decimal_places=2)
    recorded_date = models.DateField()
    recorded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    station = models.CharField(max_length=100, blank=True)
    preventive_action = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.item.name} - {self.waste_quantity} {self.unit} ({self.waste_type})"
