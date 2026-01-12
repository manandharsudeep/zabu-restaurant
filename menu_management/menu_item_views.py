from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from orders.models import MenuItem, Category
from django.db import IntegrityError

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
@user_passes_test(is_admin)
def create_menu_item(request):
    """Create a new menu item"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        category_id = request.POST.get('category')
        preparation_time = request.POST.get('preparation_time', 15)
        available = request.POST.get('available') == 'on'
        
        # Validation
        if not all([name, description, price, category_id]):
            messages.error(request, 'All required fields must be filled out.')
            return render(request, 'menu_management/create_menu_item.html', {
                'form_data': request.POST,
                'categories': Category.objects.all()
            })
        
        try:
            # Create menu item
            category = get_object_or_404(Category, id=category_id)
            menu_item = MenuItem.objects.create(
                name=name,
                description=description,
                price=price,
                category=category,
                preparation_time=preparation_time,
                available=available
            )
            
            messages.success(request, f'Menu item "{name}" created successfully!')
            return redirect('menu_management:menu_list')
            
        except IntegrityError:
            messages.error(request, 'A menu item with this name already exists in this category.')
            return render(request, 'menu_management/create_menu_item.html', {
                'form_data': request.POST,
                'categories': Category.objects.all()
            })
        except Exception as e:
            messages.error(request, f'Error creating menu item: {str(e)}')
            return render(request, 'menu_management/create_menu_item.html', {
                'form_data': request.POST,
                'categories': Category.objects.all()
            })
    
    return render(request, 'menu_management/create_menu_item.html', {
        'form_data': {},
        'categories': Category.objects.all()
    })

@login_required
@user_passes_test(is_admin)
def menu_item_list(request):
    """List all menu items"""
    menu_items = MenuItem.objects.select_related('category').all().order_by('category__name', 'name')
    return render(request, 'menu_management/menu_item_list.html', {
        'menu_items': menu_items
    })
