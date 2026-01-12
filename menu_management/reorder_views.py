from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from menu_management.inventory_models import InventoryItem, StorageLocation
from orders.models import Category, MenuItem
from django.db import IntegrityError
from decimal import Decimal

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
@user_passes_test(is_admin)
def create_reorder_item(request):
    """Create a reorder item for inventory restocking"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        supplier_info = request.POST.get('supplier_info')
        unit_cost = request.POST.get('unit_cost')
        preferred_vendor = request.POST.get('preferred_vendor')
        reorder_level = request.POST.get('reorder_level')
        max_stock = request.POST.get('max_stock')
        storage_location_id = request.POST.get('storage_location')
        notes = request.POST.get('notes')
        
        # Validation
        if not all([name, description, category_id, unit_cost]):
            messages.error(request, 'All required fields must be filled out.')
            return render(request, 'menu_management/create_reorder_item.html', {
                'form_data': request.POST,
                'categories': Category.objects.all(),
                'storage_locations': StorageLocation.objects.all()
            })
        
        try:
            # Create inventory item for reordering
            category = get_object_or_404(Category, id=category_id)
            storage_location = get_object_or_404(StorageLocation, id=storage_location_id) if storage_location_id else None
            
            inventory_item = InventoryItem.objects.create(
                name=name,
                description=description,
                category=category.name,
                supplier_info=supplier_info,
                unit_cost=Decimal(unit_cost),
                preferred_vendor=preferred_vendor,
                reorder_level=int(reorder_level) if reorder_level else 10,
                max_stock=int(max_stock) if max_stock else 100,
                storage_location=storage_location,
                current_stock=0,  # Start with 0, will be updated when received
                notes=notes,
                is_active=True
            )
            
            messages.success(request, f'Reorder item "{name}" created successfully!')
            return redirect('menu_management:inventory_items')
            
        except IntegrityError:
            messages.error(request, 'An item with this name already exists.')
            return render(request, 'menu_management/create_reorder_item.html', {
                'form_data': request.POST,
                'categories': Category.objects.all(),
                'storage_locations': StorageLocation.objects.all()
            })
        except Exception as e:
            messages.error(request, f'Error creating reorder item: {str(e)}')
            return render(request, 'menu_management/create_reorder_item.html', {
                'form_data': request.POST,
                'categories': Category.objects.all(),
                'storage_locations': StorageLocation.objects.all()
            })
    
    return render(request, 'menu_management/create_reorder_item.html', {
        'form_data': {},
        'categories': Category.objects.all(),
        'storage_locations': StorageLocation.objects.all()
    })

@login_required
@user_passes_test(is_admin)
def reorder_items_list(request):
    """List all reorder items"""
    items = InventoryItem.objects.select_related('storage_location').all().order_by('name')
    return render(request, 'menu_management/reorder_items_list.html', {
        'items': items
    })
