from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

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

class Menu(models.Model):
    MENU_TYPES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('bar', 'Bar'),
        ('dessert', 'Dessert'),
        ('catering', 'Catering'),
        ('seasonal', 'Seasonal'),
        ('tasting', 'Tasting'),
    ]
    
    name = models.CharField(max_length=200)
    menu_type = models.CharField(max_length=20, choices=MENU_TYPES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
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
