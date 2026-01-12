from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from orders.models import Order, OrderItem, OrderStatusUpdate
from datetime import datetime, timedelta

@login_required
def order_dashboard(request):
    """Main order dashboard for admin"""
    # Get order statistics
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    preparing_orders = Order.objects.filter(status='preparing').count()
    ready_orders = Order.objects.filter(status='ready').count()
    completed_today = Order.objects.filter(
        status='completed', 
        updated_at__date=timezone.now().date()
    ).count()
    
    # Get recent orders
    recent_orders = Order.objects.all().order_by('-created_at')[:10]
    
    # Get overdue orders
    overdue_orders = [order for order in Order.objects.filter(
        status__in=['pending', 'confirmed', 'preparing']
    ) if order.is_overdue]
    
    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
        'completed_today': completed_today,
        'recent_orders': recent_orders,
        'overdue_orders': overdue_orders,
    }
    return render(request, 'admin/order_dashboard.html', context)

@login_required
def order_list(request):
    """List all orders with filtering"""
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    search_query = request.GET.get('search', '')
    
    orders = Order.objects.all().order_by('-created_at')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if priority_filter:
        orders = orders.filter(priority=priority_filter)
    
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(customer_name__icontains=search_query) |
            Q(table_number__icontains=search_query)
        )
    
    # Get available staff for assignment
    staff_users = User.objects.filter(is_staff=True).order_by('username')
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'search_query': search_query,
        'staff_users': staff_users,
    }
    return render(request, 'admin/order_list.html', context)

@login_required
def order_detail(request, order_id):
    """Detailed view of a single order"""
    order = get_object_or_404(Order, id=order_id)
    order_items = order.items.all()
    status_updates = order.status_updates.all().order_by('-timestamp')
    
    # Get available staff for assignment
    staff_users = User.objects.filter(is_staff=True).order_by('username')
    
    context = {
        'order': order,
        'order_items': order_items,
        'status_updates': status_updates,
        'staff_users': staff_users,
    }
    return render(request, 'admin/order_detail.html', context)

@login_required
def update_order_status(request, order_id):
    """Update order status"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if new_status in dict(Order.STATUS_CHOICES):
            # Create status update record
            OrderStatusUpdate.objects.create(
                order=order,
                status=new_status,
                updated_by=request.user,
                notes=notes
            )
            
            # Update order status
            order.status = new_status
            order.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Order status updated to {new_status}'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid status'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def assign_order(request, order_id):
    """Assign order to staff member"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        staff_id = request.POST.get('staff_id')
        
        if staff_id:
            staff = get_object_or_404(User, id=staff_id)
            order.assigned_to = staff
            order.save()
            
            # Create status update
            OrderStatusUpdate.objects.create(
                order=order,
                status=order.status,
                updated_by=request.user,
                notes=f'Order assigned to {staff.username}'
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Order assigned to {staff.username}'
            })
        else:
            order.assigned_to = None
            order.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Order assignment removed'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def set_order_priority(request, order_id):
    """Set order priority"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        priority = request.POST.get('priority')
        
        if priority in dict(Order.PRIORITY_CHOICES):
            order.priority = priority
            order.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Order priority set to {priority}'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid priority'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def set_estimated_time(request, order_id):
    """Set estimated completion time"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        time_str = request.POST.get('estimated_time')
        
        try:
            # Parse time string (format: "HH:MM")
            hours, minutes = map(int, time_str.split(':'))
            estimated_time = datetime.time(hours, minutes)
            order.estimated_time = estimated_time
            order.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Estimated time set to {time_str}'
            })
        except (ValueError, AttributeError):
            return JsonResponse({
                'success': False,
                'message': 'Invalid time format'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def order_statistics(request):
    """Order statistics for dashboard"""
    # Get orders from last 7 days
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_orders = Order.objects.filter(created_at__gte=seven_days_ago)
    
    # Daily order counts
    daily_stats = {}
    for i in range(7):
        date = (timezone.now() - timedelta(days=i)).date()
        daily_stats[date.strftime('%Y-%m-%d')] = Order.objects.filter(
            created_at__date=date
        ).count()
    
    # Status distribution
    status_stats = {}
    for status, label in Order.STATUS_CHOICES:
        status_stats[status] = Order.objects.filter(status=status).count()
    
    # Priority distribution
    priority_stats = {}
    for priority, label in Order.PRIORITY_CHOICES:
        priority_stats[priority] = Order.objects.filter(priority=priority).count()
    
    return JsonResponse({
        'daily_stats': daily_stats,
        'status_stats': status_stats,
        'priority_stats': priority_stats,
        'total_orders': Order.objects.count(),
        'recent_orders': recent_orders.count(),
    })
