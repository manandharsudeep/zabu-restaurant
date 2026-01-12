from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.http import JsonResponse
from django.urls import reverse
from .models import Category, MenuItem, Order, OrderItem
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from menu_management.enhanced_course_menu_models import CourseMenuTemplate


def gateway_view(request):
    """Main gateway page for Zabu Restaurant"""
    # Redirect admin/superusers to unified management dashboard
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('menu_management:unified_management')
    
    # Get featured course menus (first 6 available course menu templates)
    featured_course_menus = CourseMenuTemplate.objects.filter(is_active=True).order_by('name')[:6]
    
    # Get cart count for navigation
    cart = request.session.get('cart', {})
    cart_count = sum(cart.values())
    
    context = {
        'featured_course_menus': featured_course_menus,
        'cart_count': cart_count,
    }
    return render(request, 'gateway.html', context)


def staff_login(request):
    """Handle staff authentication"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect admin/superusers to unified management dashboard
            if user.is_superuser:
                return redirect('menu_management:unified_management')
            
            # Redirect regular staff to staff portal
            return redirect('staff_portal')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions.')
    
    return render(request, 'staff_login.html')


def staff_portal_view(request):
    """Staff portal landing page"""
    if not request.user.is_authenticated or not request.user.is_staff:
        return render(request, 'staff_portal.html')
    
    return render(request, 'staff_portal.html')


def staff_logout(request):
    """Handle staff logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('gateway')


def customer_signup(request):
    """Handle customer registration"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to Zabu Restaurant, {user.first_name}!')
            
            # Redirect to intended page or menu
            next_url = request.GET.get('next', 'menu')
            return redirect(next_url)
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'signup.html', {'form': form})


def customer_login(request):
    """Handle customer login"""
    if request.method == 'POST':
        form = CustomAuthenticationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                
                # Redirect to intended page or menu
                next_url = request.GET.get('next', 'menu')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'login.html', {'form': form})


def customer_logout(request):
    """Handle customer logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('gateway')


def menu_view(request):
    # Only redirect staff users (not admin/superusers) to staff portal
    if request.user.is_authenticated and request.user.is_staff and not request.user.is_superuser:
        return redirect('staff_portal')
    
    categories = Category.objects.all()
    menu_items = MenuItem.objects.filter(available=True).select_related('category')
    
    cart = request.session.get('cart', {})
    cart_count = sum(cart.values())
    
    context = {
        'categories': categories,
        'menu_items': menu_items,
        'cart_count': cart_count,
    }
    return render(request, 'menu.html', context)


def add_to_cart(request, item_id):
    menu_item = get_object_or_404(MenuItem, id=item_id, available=True)
    
    cart = request.session.get('cart', {})
    item_id_str = str(item_id)
    
    if item_id_str in cart:
        cart[item_id_str] += 1
    else:
        cart[item_id_str] = 1
    
    request.session['cart'] = cart
    messages.success(request, f'{menu_item.name} added to cart!')
    
    return redirect('menu')


def view_cart(request):
    # Only redirect staff users (not admin/superusers) to staff portal
    if request.user.is_authenticated and request.user.is_staff and not request.user.is_superuser:
        return redirect('staff_portal')
    
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    
    for item_id, quantity in cart.items():
        menu_item = get_object_or_404(MenuItem, id=item_id)
        item_total = menu_item.price * quantity
        cart_items.append({
            'menu_item': menu_item,
            'quantity': quantity,
            'total_price': item_total,
        })
        total += item_total
    
    context = {
        'cart_items': cart_items,
        'total': total,
        'cart_count': sum(cart.values()),
    }
    return render(request, 'cart.html', context)


def update_cart(request, item_id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        item_id_str = str(item_id)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity > 0:
            cart[item_id_str] = quantity
        else:
            cart.pop(item_id_str, None)
        
        request.session['cart'] = cart
        messages.success(request, 'Cart updated!')
    
    return redirect('view_cart')


def remove_from_cart(request, item_id):
    cart = request.session.get('cart', {})
    item_id_str = str(item_id)
    
    if item_id_str in cart:
        menu_item = get_object_or_404(MenuItem, id=item_id)
        del cart[item_id_str]
        request.session['cart'] = cart
        messages.success(request, f'{menu_item.name} removed from cart!')
    
    return redirect('view_cart')


def checkout(request):
    """Handle checkout with payment processing"""
    cart = request.session.get('cart', {})
    
    if not cart:
        messages.error(request, 'Your cart is empty!')
        return redirect('view_cart')
    
    # Get cart items
    cart_items = []
    total = 0
    for item_id, quantity in cart.items():
        menu_item = get_object_or_404(MenuItem, id=item_id, available=True)
        item_total = menu_item.price * quantity
        cart_items.append({
            'menu_item': menu_item,
            'quantity': quantity,
            'total_price': item_total,
        })
        total += item_total
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'cash')
        
        # Allow cash purchases, block other payment methods
        if payment_method != 'cash':
            messages.error(request, ' Payment processing is currently not implemented for this payment method. Please choose "Cash on Delivery" and try again.')
            return redirect('checkout')
        
        customer_name = request.POST.get('customer_name')
        customer_phone = request.POST.get('customer_phone')
        table_number = request.POST.get('table_number')
        notes = request.POST.get('notes')
        
        if not customer_name:
            messages.error(request, 'Please provide your name!')
            return redirect('view_cart')
        
        # Create order for cash payment
        order = Order.objects.create(
            customer_name=customer_name,
            customer_phone=customer_phone,
            table_number=table_number,
            notes=notes,
            payment_method='cash',
        )
        
        # Add items to order
        for item_id, quantity in cart.items():
            menu_item = get_object_or_404(MenuItem, id=item_id)
            order_item = OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                quantity=quantity,
            )
        
        order.total_amount = total
        order.save()
        
        # Clear cart
        request.session['cart'] = {}
        
        messages.success(request, f'Order placed successfully! Your order number is {order.order_number}. Please pay cash on delivery.')
        return redirect(f'{reverse("order_status")}?order_number={order.order_number}')
    
    context = {
        'cart_items': cart_items,
        'total': total,
    }
    return render(request, 'checkout.html', context)


def order_status(request):
    order_number = request.GET.get('order_number')
    order = None
    
    if order_number:
        # Remove # prefix if present and convert to uppercase
        clean_order_number = order_number.replace('#', '').upper()
        try:
            order = Order.objects.get(order_number=clean_order_number)
        except Order.DoesNotExist:
            order = None
    
    context = {
        'order': order,
        'order_number': order_number,
    }
    return render(request, 'order_status.html', context)


def kitchen_display(request):
    """Main kitchen display - redirect to new kitchen dashboard"""
    return redirect('kitchen_dashboard')


def update_order_status(request, order_id, new_status):
    order = get_object_or_404(Order, id=order_id)
    
    valid_statuses = ['pending', 'confirmed', 'preparing', 'ready', 'completed', 'cancelled']
    if new_status in valid_statuses:
        order.status = new_status
        order.save()
        messages.success(request, f'Order {order.order_number} status updated to {order.get_status_display()}')
    else:
        messages.error(request, 'Invalid status!')
    
    return redirect('kitchen_display')
