from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from orders.models import MenuItem, Category, Order, OrderItem
from menu_management.enhanced_course_menu_models import CourseMenuTemplate, CourseMenuInstance
from menu_management.models import Recipe, RecipeMenuItemLink
from decimal import Decimal
import json

def customer_course_menu(request):
    """Customer-facing course menu selection page"""
    
    # Get all active course menu templates
    course_menus = CourseMenuTemplate.objects.filter(is_active=True).order_by('name')
    
    # Organize course menus by type
    menu_data = []
    for menu in course_menus:
        # Check if menu is available (seasonal, etc.)
        is_available = True
        
        # Check seasonal availability
        if menu.is_seasonal and menu.season_months:
            current_month = timezone.now().month
            if current_month not in menu.season_months:
                is_available = False
        
        menu_data.append({
            'id': menu.template_id,
            'name': menu.name,
            'description': menu.description,
            'menu_type': menu.get_menu_type_display(),
            'course_count': menu.course_count,
            'base_price': menu.base_price,
            'price_per_person': menu.price_per_person,
            'min_party_size': menu.min_party_size,
            'max_party_size': menu.max_party_size,
            'estimated_duration': menu.estimated_duration,
            'vegetarian_available': menu.vegetarian_available,
            'vegan_available': menu.vegan_available,
            'gluten_free_available': menu.gluten_free_available,
            'wine_pairing_available': menu.wine_pairing_available,
            'is_available': is_available,
            'advance_booking_days': menu.advance_booking_days,
            'chef_table_exclusive': menu.chef_table_exclusive
        })
    
    context = {
        'course_menus': menu_data,
        'user_authenticated': request.user.is_authenticated,
        'cart_items': get_cart_items(request) if request.user.is_authenticated else []
    }
    
    return render(request, 'customer/course_menu.html', context)

@login_required
@require_POST
def add_to_cart(request):
    """Add course menu to customer cart"""
    
    try:
        data = json.loads(request.body)
        menu_template_id = data.get('menu_template_id')
        party_size = data.get('party_size', 1)
        dietary_requirements = data.get('dietary_requirements', [])
        
        course_menu = get_object_or_404(CourseMenuTemplate, template_id=menu_template_id, is_active=True)
        
        # Validate party size
        if party_size < course_menu.min_party_size or party_size > course_menu.max_party_size:
            return JsonResponse({
                'success': False,
                'message': f'Party size must be between {course_menu.min_party_size} and {course_menu.max_party_size}'
            })
        
        # Get or create cart from session
        cart = request.session.get('course_cart', {})
        
        # Add course menu to cart
        item_key = str(menu_template_id)
        if item_key in cart:
            return JsonResponse({
                'success': False,
                'message': 'This course menu is already in your cart'
            })
        else:
            cart[item_key] = {
                'name': course_menu.name,
                'menu_type': course_menu.get_menu_type_display(),
                'price_per_person': str(course_menu.price_per_person),
                'party_size': party_size,
                'total_price': str(course_menu.price_per_person * party_size),
                'dietary_requirements': dietary_requirements,
                'course_count': course_menu.course_count,
                'estimated_duration': course_menu.estimated_duration
            }
        
        # Update session
        request.session['course_cart'] = cart
        request.session.modified = True
        
        return JsonResponse({
            'success': True,
            'message': f'{course_menu.name} added to cart',
            'cart_count': len(cart)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
def view_cart(request):
    """View customer course menu cart"""
    
    cart = request.session.get('course_cart', {})
    cart_items = []
    total_price = Decimal('0.00')
    
    for menu_id, item_data in cart.items():
        item_total = Decimal(item_data['total_price'])
        total_price += item_total
        
        cart_items.append({
            'id': menu_id,
            'name': item_data['name'],
            'menu_type': item_data['menu_type'],
            'price_per_person': Decimal(item_data['price_per_person']),
            'party_size': item_data['party_size'],
            'total_price': item_total,
            'course_count': item_data['course_count'],
            'estimated_duration': item_data['estimated_duration'],
            'dietary_requirements': item_data.get('dietary_requirements', [])
        })
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'cart_count': len(cart_items)
    }
    
    return render(request, 'customer/cart.html', context)

@login_required
@require_POST
def update_cart(request):
    """Update course menu cart party size"""
    
    try:
        data = json.loads(request.body)
        menu_template_id = data.get('menu_template_id')
        party_size = data.get('party_size', 1)
        
        cart = request.session.get('course_cart', {})
        item_key = str(menu_template_id)
        
        if item_key in cart:
            # Get the course menu to validate party size
            course_menu = get_object_or_404(CourseMenuTemplate, template_id=menu_template_id, is_active=True)
            
            if party_size < course_menu.min_party_size or party_size > course_menu.max_party_size:
                return JsonResponse({
                    'success': False,
                    'message': f'Party size must be between {course_menu.min_party_size} and {course_menu.max_party_size}'
                })
            
            if party_size > 0:
                cart[item_key]['party_size'] = party_size
                cart[item_key]['total_price'] = str(course_menu.price_per_person * party_size)
            else:
                del cart[item_key]
            
            request.session['course_cart'] = cart
            request.session.modified = True
            
            # Calculate new totals
            total_price = sum(Decimal(item['total_price']) for item in cart.values())
            cart_count = len(cart)
            
            return JsonResponse({
                'success': True,
                'total_price': str(total_price),
                'cart_count': cart_count
            })
        
        return JsonResponse({'success': False, 'message': 'Course menu not found in cart'})
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
def checkout(request):
    """Checkout page for placing course menu orders"""
    
    cart = request.session.get('course_cart', {})
    
    if not cart:
        messages.warning(request, 'Your cart is empty')
        return redirect('customer_course_menu')
    
    cart_items = []
    total_price = Decimal('0.00')
    
    for menu_id, item_data in cart.items():
        item_total = Decimal(item_data['total_price'])
        total_price += item_total
        
        cart_items.append({
            'id': menu_id,
            'name': item_data['name'],
            'menu_type': item_data['menu_type'],
            'price_per_person': Decimal(item_data['price_per_person']),
            'party_size': item_data['party_size'],
            'total_price': item_total,
            'course_count': item_data['course_count'],
            'estimated_duration': item_data['estimated_duration'],
            'dietary_requirements': item_data.get('dietary_requirements', [])
        })
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'user': request.user
    }
    
    return render(request, 'customer/checkout.html', context)

@login_required
@require_POST
def place_order(request):
    """Place the course menu order"""
    
    try:
        cart = request.session.get('course_cart', {})
        
        if not cart:
            messages.error(request, 'Your cart is empty')
            return redirect('customer_course_menu')
        
        # Create order
        order = Order.objects.create(
            customer=request.user,
            status='pending',
            total_amount=Decimal('0.00')
        )
        
        total_amount = Decimal('0.00')
        
        # Add course menu instances to order
        for menu_id, item_data in cart.items():
            course_menu = get_object_or_404(CourseMenuTemplate, template_id=menu_id, is_active=True)
            party_size = item_data['party_size']
            total_price = Decimal(item_data['total_price'])
            
            # Create course menu instance
            menu_instance = CourseMenuInstance.objects.create(
                template=course_menu,
                name=f"{course_menu.name} - Party of {party_size}",
                table_number="TBD",  # Will be assigned by staff
                customer_count=party_size,
                final_price_per_person=Decimal(item_data['price_per_person']),
                total_price=total_price,
                dietary_requirements=item_data.get('dietary_requirements', []),
                status='booked'
            )
            
            # Create a dummy menu item for the order (since OrderItem requires it)
            # We'll use the first menu item as a placeholder
            dummy_menu_item = MenuItem.objects.first()
            if not dummy_menu_item:
                # Create a dummy menu item if none exists
                dummy_menu_item = MenuItem.objects.create(
                    category=Category.objects.first(),
                    name="Course Menu",
                    description="Course Menu Order",
                    price=total_price,
                    available=True
                )
            
            # Create order item with course menu info in notes
            OrderItem.objects.create(
                order=order,
                menu_item=dummy_menu_item,
                quantity=1,
                price=total_price,
                notes=f"Course Menu: {course_menu.name} | Instance ID: {menu_instance.instance_id} | Party Size: {party_size}"
            )
            
            total_amount += total_price
        
        # Update order total
        order.total_amount = total_amount
        order.save()
        
        # Clear cart
        request.session['course_cart'] = {}
        request.session.modified = True
        
        messages.success(request, f'Order #{order.id} placed successfully!')
        return redirect('order_confirmation', order_id=order.id)
        
    except Exception as e:
        messages.error(request, f'Error placing order: {str(e)}')
        return redirect('checkout')

def order_confirmation(request, order_id):
    """Order confirmation page for course menu orders"""
    
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    order_items = order.orderitem_set.select_related('menu_item').all()
    
    # Parse course menu information from notes
    course_menu_items = []
    for item in order_items:
        if "Course Menu:" in item.notes:
            # Parse course menu info from notes
            notes_parts = item.notes.split(" | ")
            menu_name = notes_parts[0].replace("Course Menu: ", "")
            instance_id = notes_parts[1].replace("Instance ID: ", "")
            party_size = notes_parts[2].replace("Party Size: ", "")
            
            course_menu_items.append({
                'menu_name': menu_name,
                'instance_id': instance_id,
                'party_size': party_size,
                'price': item.price,
                'quantity': item.quantity
            })
        else:
            # Regular menu item
            course_menu_items.append({
                'menu_name': item.menu_item.name,
                'instance_id': None,
                'party_size': item.quantity,
                'price': item.price,
                'quantity': item.quantity
            })
    
    context = {
        'order': order,
        'order_items': course_menu_items
    }
    
    return render(request, 'customer/order_confirmation.html', context)

def get_cart_items(request):
    """Helper function to get course menu cart items"""
    cart = request.session.get('course_cart', {})
    return [
        {
            'id': item_id,
            'name': item_data['name'],
            'party_size': item_data['party_size'],
            'total_price': Decimal(item_data['total_price'])
        } for item_id, item_data in cart.items()
    ]
