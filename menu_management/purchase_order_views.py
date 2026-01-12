from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
import json

from .inventory_models import *
from .models import *

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@user_passes_test(is_admin)
def create_purchase_order(request):
    """Create a new purchase order"""
    if request.method == 'POST':
        try:
            # Get form data
            vendor_id = request.POST.get('vendor')
            expected_date = request.POST.get('expected_date')
            delivery_address = request.POST.get('delivery_address', 'Restaurant Address')
            notes = request.POST.get('notes', '')
            items_data = request.POST.get('items_data', '{}')
            
            # Validate vendor
            vendor = get_object_or_404(Vendor, id=vendor_id)
            
            # Parse items data
            items = json.loads(items_data)
            
            # Generate PO number
            from datetime import datetime
            po_number = f"PO-{datetime.now().strftime('%Y%m%d')}-{PurchaseOrder.objects.count() + 1:04d}"
            
            # Create purchase order
            purchase_order = PurchaseOrder.objects.create(
                po_number=po_number,
                vendor=vendor,
                expected_date=expected_date,
                delivery_address=delivery_address,
                notes=notes,
                created_by=request.user,
                status='draft'
            )
            
            # Add items to purchase order
            subtotal = 0
            for item_data in items:
                item = get_object_or_404(InventoryItem, id=item_data['item_id'])
                quantity = Decimal(str(item_data['quantity']))
                unit_price = Decimal(str(item_data['unit_price']))
                total_price = quantity * unit_price
                
                PurchaseOrderItem.objects.create(
                    po=purchase_order,
                    item=item,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price
                )
                subtotal += total_price
            
            # Calculate totals (assuming 10% tax)
            tax = subtotal * Decimal('0.10')
            total = subtotal + tax
            
            purchase_order.subtotal = subtotal
            purchase_order.tax = tax
            purchase_order.total = total
            purchase_order.save()
            
            messages.success(request, f'Purchase Order {po_number} created successfully!')
            return redirect('menu_management:purchase_orders')
            
        except Exception as e:
            messages.error(request, f'Error creating purchase order: {str(e)}')
            return redirect('menu_management:create_purchase_order')
    
    # GET request - show creation form
    vendors = Vendor.objects.all()
    items = InventoryItem.objects.filter(is_active=True).order_by('category', 'name')
    
    context = {
        'vendors': vendors,
        'items': items,
    }
    return render(request, 'menu_management/create_purchase_order.html', context)


@login_required
@user_passes_test(is_admin)
def purchase_order_detail(request, po_id):
    """View and manage a specific purchase order"""
    purchase_order = get_object_or_404(PurchaseOrder, id=po_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            purchase_order.status = 'approved'
            purchase_order.approved_by = request.user
            purchase_order.approved_at = timezone.now()
            purchase_order.save()
            messages.success(request, f'Purchase Order {purchase_order.po_number} approved!')
            
        elif action == 'send':
            purchase_order.status = 'sent'
            purchase_order.save()
            messages.success(request, f'Purchase Order {purchase_order.po_number} sent to vendor!')
            
        elif action == 'receive':
            purchase_order.status = 'received'
            purchase_order.save()
            messages.success(request, f'Purchase Order {purchase_order.po_number} marked as received!')
            
        elif action == 'cancel':
            purchase_order.status = 'cancelled'
            purchase_order.save()
            messages.success(request, f'Purchase Order {purchase_order.po_number} cancelled!')
        
        return redirect('menu_management:purchase_order_detail', po_id=po_id)
    
    context = {
        'purchase_order': purchase_order,
    }
    return render(request, 'menu_management/purchase_order_detail.html', context)
