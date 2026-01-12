from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from orders.models import Order, OrderItem, OrderStatusUpdate
from datetime import datetime, timedelta

@login_required
def kitchen_dashboard(request):
    """Kitchen dashboard for order management"""
    from django.utils import timezone
    
    # Get active orders (pending, confirmed, preparing)
    active_orders = Order.objects.filter(
        status__in=['pending', 'confirmed', 'preparing']
    ).order_by('priority', 'created_at')
    
    # Get ready orders
    ready_orders = Order.objects.filter(status='ready').order_by('-updated_at')[:10]
    
    # Get orders assigned to current user
    my_orders = Order.objects.filter(
        assigned_to=request.user,
        status__in=['pending', 'confirmed', 'preparing']
    ).order_by('priority', 'created_at')
    
    # Calculate completed today
    completed_today = Order.objects.filter(
        status='completed',
        updated_at__date=timezone.now().date()
    ).count()
    
    context = {
        'active_orders': active_orders,
        'ready_orders': ready_orders,
        'my_orders': my_orders,
        'completed_today': completed_today,
    }
    return render(request, 'kitchen/kitchen_dashboard.html', context)

@login_required
def kitchen_order_detail(request, order_id):
    """Kitchen view for order details"""
    order = get_object_or_404(Order, id=order_id)
    order_items = order.items.all()
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'kitchen/kitchen_order_detail.html', context)

@login_required
def start_preparation(request, order_id):
    """Start preparing an order"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        
        # Update status to preparing
        order.status = 'preparing'
        order.assigned_to = request.user
        order.save()
        
        # Create status update
        OrderStatusUpdate.objects.create(
            order=order,
            status='preparing',
            updated_by=request.user,
            notes='Preparation started'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Preparation started'
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def mark_ready(request, order_id):
    """Mark order as ready"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        
        # Update status to ready
        order.status = 'ready'
        order.save()
        
        # Create status update
        OrderStatusUpdate.objects.create(
            order=order,
            status='ready',
            updated_by=request.user,
            notes='Order is ready for pickup/delivery'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Order marked as ready'
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def complete_order(request, order_id):
    """Complete an order"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        
        # Update status to completed
        order.status = 'completed'
        order.save()
        
        # Create status update
        OrderStatusUpdate.objects.create(
            order=order,
            status='completed',
            updated_by=request.user,
            notes='Order completed'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Order completed'
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def kitchen_queue(request):
    """Kitchen order queue view"""
    # Filter orders
    status_filter = request.GET.get('status', 'active')
    priority_filter = request.GET.get('priority', '')
    
    if status_filter == 'active':
        orders = Order.objects.filter(
            status__in=['pending', 'confirmed', 'preparing']
        )
    elif status_filter == 'ready':
        orders = Order.objects.filter(status='ready')
    elif status_filter == 'my':
        orders = Order.objects.filter(
            assigned_to=request.user,
            status__in=['pending', 'confirmed', 'preparing']
        )
    else:
        orders = Order.objects.all()
    
    if priority_filter:
        orders = orders.filter(priority=priority_filter)
    
    orders = orders.order_by('priority', 'created_at')
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
    }
    return render(request, 'kitchen/kitchen_queue.html', context)

@login_required
def add_order_note(request, order_id):
    """Add note to order"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        note = request.POST.get('note', '')
        
        if note:
            # Create status update with note
            OrderStatusUpdate.objects.create(
                order=order,
                status=order.status,
                updated_by=request.user,
                notes=note
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Note added'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})
