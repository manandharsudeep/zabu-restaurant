from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"


class MenuItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='menu_items')
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='menu_images/', blank=True, null=True)
    available = models.BooleanField(default=True)
    preparation_time = models.IntegerField(help_text="Time in minutes", default=15)
    
    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('online', 'Online Payment'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    order_number = models.CharField(max_length=20, unique=True)
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20, blank=True)
    table_number = models.CharField(max_length=10, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    estimated_time = models.TimeField(null=True, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_orders')
    
    def __str__(self):
        return f"Order #{self.order_number}"
    
    @property
    def time_elapsed(self):
        if self.created_at:
            from datetime import datetime
            elapsed = datetime.now() - self.created_at.replace(tzinfo=None)
            return int(elapsed.total_seconds() / 60)  # minutes
        return 0
    
    @property
    def is_overdue(self):
        if self.estimated_time and self.status in ['pending', 'confirmed', 'preparing']:
            from datetime import datetime, time
            now = datetime.now().time()
            if now > self.estimated_time:
                return True
        return False
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            last_order = Order.objects.all().order_by('id').last()
            if last_order:
                last_number = int(last_order.order_number[3:])
                self.order_number = f"ORD{last_number + 1:04d}"
            else:
                self.order_number = "ORD0001"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"
    
    @property
    def total_price(self):
        return self.price * self.quantity
    
    def save(self, *args, **kwargs):
        self.price = self.menu_item.price
        super().save(*args, **kwargs)


# Reservation Models
class Table(models.Model):
    """Restaurant table management"""
    table_number = models.CharField(max_length=10, unique=True)
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(20)])
    table_type = models.CharField(max_length=20, choices=[
        ('standard', 'Standard'),
        ('booth', 'Booth'),
        ('private', 'Private'),
        ('outdoor', 'Outdoor'),
        ('bar', 'Bar'),
    ], default='standard')
    location = models.CharField(max_length=50, choices=[
        ('main_dining', 'Main Dining Room'),
        ('private_room', 'Private Room'),
        ('outdoor_patio', 'Outdoor Patio'),
        ('bar_area', 'Bar Area'),
        ('lounge', 'Lounge'),
    ], default='main_dining')
    is_available = models.BooleanField(default=True)
    min_party_size = models.PositiveIntegerField(default=1)
    max_party_size = models.PositiveIntegerField(default=8)
    
    def __str__(self):
        return f"Table {self.table_number} ({self.capacity} seats)"
    
    class Meta:
        ordering = ['table_number']

class TableReservation(models.Model):
    """Individual table reservations"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    party_size = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(20)])
    occasion = models.CharField(max_length=50, choices=[
        ('casual', 'Casual Dining'),
        ('business', 'Business Meeting'),
        ('celebration', 'Celebration'),
        ('date_night', 'Date Night'),
        ('family', 'Family Gathering'),
        ('romantic', 'Romantic Dinner'),
        ('special_occasion', 'Special Occasion'),
    ], blank=True)
    special_requests = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('seated', 'Seated'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmation_code = models.CharField(max_length=8, unique=True)
    
    def __str__(self):
        return f"Reservation {self.confirmation_code} - {self.table.table_number} on {self.date} at {self.time}"
    
    def save(self, *args, **kwargs):
        if not self.confirmation_code:
            self.confirmation_code = self.generate_confirmation_code()
        super().save(*args, **kwargs)
    
    def generate_confirmation_code(self):
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    class Meta:
        ordering = ['date', 'time']

class VenueReservation(models.Model):
    """Whole venue reservations for private events"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    event_name = models.CharField(max_length=100)
    event_type = models.CharField(max_length=50, choices=[
        ('wedding', 'Wedding Reception'),
        ('corporate', 'Corporate Event'),
        ('birthday', 'Birthday Party'),
        ('anniversary', 'Anniversary'),
        ('fundraiser', 'Fundraiser'),
        ('conference', 'Conference'),
        ('workshop', 'Workshop'),
        ('private_party', 'Private Party'),
    ])
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    expected_guests = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(500)])
    catering_options = models.TextField(help_text="Describe catering requirements")
    setup_requirements = models.TextField(blank=True, help_text="Special setup requirements")
    budget_range = models.CharField(max_length=50, choices=[
        ('under_1000', 'Under $1,000'),
        ('1000_5000', '$1,000 - $5,000'),
        ('5000_10000', '$5,000 - $10,000'),
        ('10000_25000', '$10,000 - $25,000'),
        ('over_25000', 'Over $25,000'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('inquiry', 'Inquiry'),
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('deposit_paid', 'Deposit Paid'),
        ('fully_paid', 'Fully Paid'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='inquiry')
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmation_code = models.CharField(max_length=10, unique=True)
    
    def __str__(self):
        return f"Venue Booking {self.confirmation_code} - {self.event_name} on {self.date}"
    
    def save(self, *args, **kwargs):
        if not self.confirmation_code:
            self.confirmation_code = self.generate_confirmation_code()
        super().save(*args, **kwargs)
    
    def generate_confirmation_code(self):
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    class Meta:
        ordering = ['date', 'start_time']

class ReservationSettings(models.Model):
    """Global reservation settings"""
    max_party_size = models.PositiveIntegerField(default=20)
    min_reservation_time = models.TimeField(default='17:00')  # 5 PM
    max_reservation_time = models.TimeField(default='23:00')  # 11 PM
    reservation_advance_days = models.PositiveIntegerField(default=90)
    auto_confirmation = models.BooleanField(default=True)
    deposit_required_venue = models.BooleanField(default=True)
    deposit_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=25.00)
    cancellation_policy = models.TextField(default="Cancellations must be made at least 24 hours in advance for a full refund.")
    
    def __str__(self):
        return "Reservation Settings"
    
    class Meta:
        verbose_name_plural = "Reservation Settings"

# Meal Pass Models
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
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price in NPR
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
    
    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('online', 'Online Payment'),
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
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash')
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
    order = models.ForeignKey('Order', on_delete=models.CASCADE, null=True, blank=True)
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

class DailyMealOption(models.Model):
    """Daily meal options for meal pass holders"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField()
    meal_option_1 = models.ForeignKey('MenuItem', on_delete=models.CASCADE, related_name='meal_option_1')
    meal_option_2 = models.ForeignKey('MenuItem', on_delete=models.CASCADE, related_name='meal_option_2')
    meal_option_3 = models.ForeignKey('MenuItem', on_delete=models.CASCADE, related_name='meal_option_3')
    meal_option_4 = models.ForeignKey('MenuItem', on_delete=models.CASCADE, related_name='meal_option_4')
    meal_option_5 = models.ForeignKey('MenuItem', on_delete=models.CASCADE, related_name='meal_option_5')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Meal options for {self.date}"
    
    class Meta:
        ordering = ['-date']

class MealPassSelection(models.Model):
    """Track daily meal selections by meal pass holders"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(MealPassSubscription, on_delete=models.CASCADE)
    daily_option = models.ForeignKey(DailyMealOption, on_delete=models.CASCADE)
    selected_meal = models.ForeignKey('MenuItem', on_delete=models.CASCADE)
    selection_date = models.DateField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.selected_meal.name} on {self.selection_date}"
    
    class Meta:
        ordering = ['-selection_date']
        unique_together = ['user', 'selection_date']

class OrderStatusUpdate(models.Model):
    """Track order status changes"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_updates')
    status = models.CharField(max_length=20)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.order.order_number} - {self.status} at {self.timestamp}"
    
    class Meta:
        ordering = ['-timestamp']


class UserProfile(models.Model):
    """Extended user profile information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, null=True, help_text="Phone number is required for meal pass purchases")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} Profile"
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
