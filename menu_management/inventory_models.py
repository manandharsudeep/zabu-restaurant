from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import uuid

class StorageLocation(models.Model):
    """Storage locations for inventory"""
    LOCATION_TYPES = [
        ('walk_in_cooler', 'Walk-in Cooler'),
        ('reach_in_cooler', 'Reach-in Cooler'),
        ('freezer', 'Freezer'),
        ('dry_storage', 'Dry Storage'),
        ('bar', 'Bar'),
        ('prep_area', 'Prep Area'),
        ('display_case', 'Display Case'),
    ]
    
    name = models.CharField(max_length=100)
    location_type = models.CharField(max_length=50, choices=LOCATION_TYPES)
    description = models.TextField(blank=True)
    capacity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Capacity in appropriate units")
    current_usage = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    temperature_required = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Required temperature in Celsius")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_location_type_display()})"
    
    @property
    def utilization_percentage(self):
        if self.capacity > 0:
            return (self.current_usage / self.capacity) * 100
        return 0

class Vendor(models.Model):
    """Supplier/vendor information"""
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    vendor_code = models.CharField(max_length=50, unique=True)
    is_preferred = models.BooleanField(default=False)
    lead_time_days = models.IntegerField(default=2)
    payment_terms = models.CharField(max_length=100, default="Net 30")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class InventoryItem(models.Model):
    """Master inventory items catalog"""
    UNIT_CHOICES = [
        ('kg', 'Kilograms'),
        ('g', 'Grams'),
        ('l', 'Liters'),
        ('ml', 'Milliliters'),
        ('pcs', 'Pieces'),
        ('box', 'Box'),
        ('case', 'Case'),
        ('bottle', 'Bottle'),
        ('jar', 'Jar'),
        ('bag', 'Bag'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=100, unique=True)
    barcode = models.CharField(max_length=50, blank=True, null=True)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    category = models.CharField(max_length=100)
    is_perishable = models.BooleanField(default=True)
    shelf_life_days = models.IntegerField(null=True, blank=True)
    storage_requirements = models.TextField(blank=True)
    standard_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    par_level = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reorder_point = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_level = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def is_below_reorder_point(self):
        total_stock = self.inventory_stocks.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
        return total_stock <= self.reorder_point

class InventoryStock(models.Model):
    """Inventory stock by location"""
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='inventory_stocks')
    location = models.ForeignKey(StorageLocation, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    reserved_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    available_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['item', 'location']
    
    def __str__(self):
        return f"{self.item.name} @ {self.location.name}: {self.quantity}"
    
    @property
    def is_critical_low(self):
        return self.available_quantity <= (self.item.reorder_point * 0.5)

class InventoryBatch(models.Model):
    """Batch/lot tracking for inventory"""
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=100)
    lot_number = models.CharField(max_length=100, blank=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.ForeignKey(StorageLocation, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    manufacture_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    received_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['item', 'batch_number']
    
    def __str__(self):
        return f"{self.item.name} - Batch {self.batch_number}"
    
    @property
    def days_until_expiration(self):
        if self.expiration_date:
            return (self.expiration_date - timezone.now().date()).days
        return None
    
    @property
    def is_expiring_soon(self):
        days = self.days_until_expiration
        return days is not None and days <= 7
    
    @property
    def is_expired(self):
        days = self.days_until_expiration
        return days is not None and days < 0

class InventoryTransaction(models.Model):
    """All inventory movements"""
    TRANSACTION_TYPES = [
        ('receive', 'Receiving'),
        ('issue', 'Issue/Usage'),
        ('transfer', 'Transfer'),
        ('adjustment', 'Adjustment'),
        ('waste', 'Waste'),
        ('return', 'Return to Vendor'),
        ('physical_count', 'Physical Count'),
    ]
    
    REASON_CODES = [
        ('normal_usage', 'Normal Usage'),
        ('spoilage', 'Spoilage'),
        ('theft', 'Theft'),
        ('damage', 'Damage'),
        ('prep_waste', 'Preparation Waste'),
        ('over_production', 'Over Production'),
        ('customer_return', 'Customer Return'),
        ('price_adjustment', 'Price Adjustment'),
        ('physical_variance', 'Physical Count Variance'),
        ('transfer_out', 'Transfer Out'),
        ('transfer_in', 'Transfer In'),
    ]
    
    transaction_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='transactions')
    batch = models.ForeignKey(InventoryBatch, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.ForeignKey(StorageLocation, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reason_code = models.CharField(max_length=50, choices=REASON_CODES, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_transaction_type_display()}: {self.item.name} ({self.quantity})"

class PurchaseOrder(models.Model):
    """Purchase orders for inventory"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('sent', 'Sent to Vendor'),
        ('partial_received', 'Partially Received'),
        ('received', 'Fully Received'),
        ('cancelled', 'Cancelled'),
    ]
    
    po_number = models.CharField(max_length=50, unique=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    order_date = models.DateTimeField(auto_now_add=True)
    expected_date = models.DateField()
    delivery_address = models.TextField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_pos')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_pos')
    
    def __str__(self):
        return f"PO-{self.po_number}"

class PurchaseOrderItem(models.Model):
    """Individual items in purchase orders"""
    po = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    received_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.item.name} - {self.quantity}"

class WasteRecord(models.Model):
    """Waste and spoilage tracking"""
    WASTE_TYPES = [
        ('spoilage', 'Spoilage'),
        ('prep_waste', 'Preparation Waste'),
        ('over_production', 'Over Production'),
        ('customer_return', 'Customer Return'),
        ('damage', 'Damage'),
        ('theft', 'Theft'),
        ('expired', 'Expired'),
    ]
    
    record_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    location = models.ForeignKey(StorageLocation, on_delete=models.CASCADE)
    batch = models.ForeignKey(InventoryBatch, on_delete=models.SET_NULL, null=True, blank=True)
    waste_type = models.CharField(max_length=20, choices=WASTE_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    reported_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_waste')
    
    def __str__(self):
        return f"{self.item.name} - {self.get_waste_type_display()} ({self.quantity})"

# Multi-Brand Inventory Allocation
# class BrandInventoryAllocation(models.Model):
#     """Virtual inventory allocation by brand"""
#     brand = models.ForeignKey('VirtualBrand', on_delete=models.CASCADE)
#     item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
#     allocated_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
#     allocated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     percentage_allocation = models.DecimalField(max_digits=5, decimal_places=2, default=0)
#     is_dedicated = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     
#     class Meta:
#         unique_together = ['brand', 'item']
#     
#     def __str__(self):
#         return f"{self.brand.name} - {self.item.name}: {self.allocated_quantity}"
