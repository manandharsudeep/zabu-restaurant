from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

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

class CourseMenuBooking(models.Model):
    """Course menu tasting reservations"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    course_menu_template = models.ForeignKey('menu_management.CourseMenuTemplate', on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    party_size = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(20)])
    dietary_restrictions = models.TextField(blank=True)
    wine_pairing = models.BooleanField(default=False)
    special_occasion = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('serving', 'Serving'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmation_code = models.CharField(max_length=8, unique=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"Course Menu {self.confirmation_code} - {self.course_menu_template.name} on {self.date}"
    
    def save(self, *args, **kwargs):
        if not self.confirmation_code:
            self.confirmation_code = self.generate_confirmation_code()
        super().save(*args, **kwargs)
    
    def generate_confirmation_code(self):
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    def calculate_total_price(self):
        base_price = self.course_menu_template.base_price
        if self.wine_pairing:
            base_price += self.course_menu_template.wine_pairing_price
        self.total_price = base_price * self.party_size
        self.save()
    
    class Meta:
        ordering = ['date', 'time']

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
