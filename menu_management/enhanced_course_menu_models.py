from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
import uuid

class CourseMenuTemplate(models.Model):
    """Predefined course menu templates"""
    
    # Menu type choices
    MENU_TYPE_CHOICES = [
        ('tasting', 'Tasting Menu'),
        ('prix_fixe', 'Prix Fixe'),
        ('chef_table', 'Chef Table'),
        ('seasonal', 'Seasonal'),
        ('holiday', 'Holiday'),
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('gluten_free', 'Gluten Free'),
    ]
    
    template_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Menu configuration
    course_count = models.IntegerField()  # 3, 5, 7, etc.
    menu_type = models.CharField(max_length=50, choices=MENU_TYPE_CHOICES)
    
    # Pricing
    base_price = models.DecimalField(max_digits=8, decimal_places=2)
    price_per_person = models.DecimalField(max_digits=8, decimal_places=2)
    price_tiers = models.JSONField(default=dict)  # Different pricing tiers
    
    # Requirements
    min_party_size = models.IntegerField(default=1)
    max_party_size = models.IntegerField(default=10)
    advance_booking_days = models.IntegerField(default=1)
    
    # Dietary accommodations
    vegetarian_available = models.BooleanField(default=True)
    vegan_available = models.BooleanField(default=False)
    gluten_free_available = models.BooleanField(default=False)
    other_dietary_options = models.JSONField(default=list)
    
    # Pairing options
    wine_pairing_available = models.BooleanField(default=False)
    beverage_pairing_available = models.BooleanField(default=False)
    sommelier_required = models.BooleanField(default=False)
    
    # Seasonal configuration
    is_seasonal = models.BooleanField(default=False)
    season_months = models.JSONField(default=list)  # [1,2,12] for winter
    holiday_specific = models.BooleanField(default=False)
    holiday_name = models.CharField(max_length=100, blank=True)
    
    # Chef configuration
    chef_table_exclusive = models.BooleanField(default=False)
    required_chef_level = models.CharField(max_length=50, default='line_cook')
    chef_notes = models.TextField(blank=True)
    
    # Timing
    estimated_duration = models.IntegerField(default=120)  # Minutes
    pacing_interval = models.IntegerField(default=15)  # Minutes between courses
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_menu_type_display()})"

class CourseMenuInstance(models.Model):
    """Individual course menu instance created from template"""
    instance_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(CourseMenuTemplate, on_delete=models.CASCADE, related_name='instances')
    
    # Status choices
    STATUS_CHOICES = [
        ('booked', 'Booked'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Instance details
    name = models.CharField(max_length=200)
    table_number = models.CharField(max_length=20)
    customer_count = models.IntegerField()
    
    # Pricing
    final_price_per_person = models.DecimalField(max_digits=8, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    pricing_tier_applied = models.CharField(max_length=50, default='standard')
    
    # Dietary accommodations
    dietary_requirements = models.JSONField(default=list)
    special_requests = models.TextField(blank=True)
    
    # Staff assignment
    server = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='served_instances')
    sommelier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sommelier_instances')
    assigned_chef = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='chef_instances')
    
    # Timing
    booking_date = models.DateField()
    booking_time = models.TimeField()
    start_time = models.DateTimeField(null=True, blank=True)
    estimated_completion = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, default='booked', choices=STATUS_CHOICES)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - Table {self.table_number}"

class CourseDefinition(models.Model):
    """Individual course within a menu"""
    course_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(CourseMenuTemplate, on_delete=models.CASCADE, related_name='courses')
    
    # Course details
    course_number = models.IntegerField()
    course_name = models.CharField(max_length=200)
    description = models.TextField()
    chef_notes = models.TextField(blank=True)
    
    # Timing
    prep_time = models.IntegerField(default=20)  # Minutes
    plating_time = models.IntegerField(default=5)  # Minutes
    presentation_time = models.IntegerField(default=2)  # Minutes
    
    # Ingredients and complexity
    main_ingredients = models.JSONField(default=list)
    complexity_level = models.CharField(max_length=20, choices=[
        ('simple', 'Simple'),
        ('medium', 'Medium'),
        ('complex', 'Complex'),
        ('chef_special', 'Chef Special'),
    ])
    
    # Dietary information
    is_vegetarian = models.BooleanField(default=False)
    is_vegan = models.BooleanField(default=False)
    is_gluten_free = models.BooleanField(default=False)
    contains_nuts = models.BooleanField(default=False)
    contains_dairy = models.BooleanField(default=False)
    allergens = models.JSONField(default=list)
    
    # Pairing information
    wine_pairing_notes = models.TextField(blank=True)
    beverage_pairing_notes = models.TextField(blank=True)
    pairing_intensity = models.CharField(max_length=20, choices=[
        ('light', 'Light'),
        ('medium', 'Medium'),
        ('bold', 'Bold'),
    ], default='medium')
    
    # Optional courses
    is_optional = models.BooleanField(default=False)
    supplement_charge = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order', 'course_number']
    
    def __str__(self):
        return f"Course {self.course_number}: {self.course_name}"

class CourseInstance(models.Model):
    """Individual course instance for a specific menu instance"""
    instance_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    menu_instance = models.ForeignKey(CourseMenuInstance, on_delete=models.CASCADE, related_name='course_instances')
    course_definition = models.ForeignKey(CourseDefinition, on_delete=models.CASCADE)
    
    # Timing
    scheduled_start = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    scheduled_completion = models.DateTimeField()
    actual_completion = models.DateTimeField(null=True, blank=True)
    
    # Kitchen coordination
    kitchen_station = models.ForeignKey('KitchenStation', on_delete=models.SET_NULL, null=True)
    plating_station = models.ForeignKey('KitchenStation', on_delete=models.SET_NULL, null=True, blank=True, related_name='plating_instances')
    
    # Status
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('served', 'Served'),
        ('skipped', 'Skipped'),
    ])
    
    # Modifications
    modifications = models.TextField(blank=True)
    dietary_substitutions = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.course_definition.course_name} - {self.menu_instance.name}"

class WinePairing(models.Model):
    """Wine pairing for courses"""
    pairing_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course_definition = models.ForeignKey(CourseDefinition, on_delete=models.CASCADE, related_name='wine_pairings')
    
    # Wine details
    wine_name = models.CharField(max_length=200)
    wine_type = models.CharField(max_length=50, choices=[
        ('red', 'Red Wine'),
        ('white', 'White Wine'),
        ('sparkling', 'Sparkling Wine'),
        ('rose', 'Rosé'),
        ('dessert', 'Dessert Wine'),
    ])
    region = models.CharField(max_length=100)
    vintage = models.IntegerField(null=True, blank=True)
    
    # Pairing details
    pairing_notes = models.TextField()
    intensity_match = models.CharField(max_length=20, choices=[
        ('light', 'Light'),
        ('medium', 'Medium'),
        ('bold', 'Bold'),
    ])
    
    # Pricing
    price_per_glass = models.DecimalField(max_digits=6, decimal_places=2)
    price_per_bottle = models.DecimalField(max_digits=8, decimal_places=2)
    
    is_available = models.BooleanField(default=True)
    is_recommended = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.wine_name} with {self.course_definition.course_name}"

class BeveragePairing(models.Model):
    """Non-alcoholic beverage pairings"""
    pairing_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course_definition = models.ForeignKey(CourseDefinition, on_delete=models.CASCADE, related_name='beverage_pairings')
    
    # Beverage details
    beverage_name = models.CharField(max_length=200)
    beverage_type = models.CharField(max_length=50, choices=[
        ('cocktail', 'Cocktail'),
        ('mocktail', 'Mocktail'),
        ('juice', 'Fresh Juice'),
        ('tea', 'Specialty Tea'),
        ('coffee', 'Specialty Coffee'),
        ('water', 'Premium Water'),
        ('soda', 'Craft Soda'),
    ])
    
    # Pairing details
    pairing_notes = models.TextField()
    intensity_match = models.CharField(max_length=20, choices=[
        ('light', 'Light'),
        ('medium', 'Medium'),
        ('bold', 'Bold'),
    ])
    
    # Pricing
    price_per_serving = models.DecimalField(max_digits=6, decimal_places=2)
    
    is_available = models.BooleanField(default=True)
    is_recommended = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.beverage_name} with {self.course_definition.course_name}"

class CourseMenuPricing(models.Model):
    """Pricing tiers for course menus"""
    pricing_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(CourseMenuTemplate, on_delete=models.CASCADE, related_name='pricing_tiers')
    
    # Tier details
    tier_name = models.CharField(max_length=50)
    tier_description = models.TextField()
    
    # Pricing
    price_per_person = models.DecimalField(max_digits=8, decimal_places=2)
    minimum_surcharge = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Conditions
    min_party_size = models.IntegerField()
    max_party_size = models.IntegerField()
    
    # Complexity factors
    ingredient_quality_multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)
    chef_level_multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)
    seasonal_multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)
    
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.tier_name} - {self.template.name}"
