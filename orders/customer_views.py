from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
from orders.models import Order, OrderItem
from django.http import JsonResponse
import json

User = get_user_model()

def is_admin(user):
    """Check if user is admin or superuser"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
@user_passes_test(is_admin)
def customer_management(request):
    """Customer management dashboard"""
    # Get all customers (non-staff users)
    customers = User.objects.filter(is_staff=False).order_by('-date_joined')
    
    # Calculate statistics
    total_customers = customers.count()
    active_customers = customers.filter(is_active=True).count()
    
    # Get recent customers (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_customers = customers.filter(date_joined__gte=thirty_days_ago).count()
    
    # Calculate customer metrics
    customer_stats = []
    for customer in customers[:10]:  # Show top 10 customers
        # Since orders don't have user field, we can't directly link them
        # We'll show customer info but order stats will be limited
        customer_stats.append({
            'customer': customer,
            'total_orders': 0,  # Can't calculate without user field
            'total_spent': 0,   # Can't calculate without user field
            'avg_order_value': 0,  # Can't calculate without user field
            'last_order': None,  # Can't calculate without user field
        })
    
    context = {
        'customers': customers,
        'customer_stats': customer_stats,
        'total_customers': total_customers,
        'active_customers': active_customers,
        'recent_customers': recent_customers,
    }
    return render(request, 'customer_management.html', context)

@login_required
@user_passes_test(is_admin)
def customer_detail(request, customer_id):
    """Detailed view of a single customer"""
    customer = get_object_or_404(User, id=customer_id, is_staff=False)
    
    # Since orders don't have user field, we can't get customer's orders
    # We'll show customer profile but order history will be empty
    orders = Order.objects.none()  # Empty queryset
    
    # Calculate customer metrics (all zero since no user field)
    total_orders = 0
    total_spent = 0
    avg_order_value = 0
    
    # Get order items breakdown (empty since no user field)
    popular_items = []
    
    # Order status breakdown (empty since no user field)
    order_status_counts = []
    
    # Monthly spending trend (empty since no user field)
    monthly_spending = []
    
    context = {
        'customer': customer,
        'orders': orders,
        'total_orders': total_orders,
        'total_spent': total_spent,
        'avg_order_value': avg_order_value,
        'popular_items': popular_items,
        'order_status_counts': order_status_counts,
        'monthly_spending': monthly_spending,
    }
    return render(request, 'customer_detail.html', context)

@login_required
@user_passes_test(is_admin)
def customer_analytics(request):
    """Customer analytics and insights"""
    customers = User.objects.filter(is_staff=False)
    orders = Order.objects.all()
    
    # Customer growth over time
    customer_growth = []
    for i in range(12):  # Last 12 months
        month_start = timezone.now() - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        month_customers = customers.filter(
            date_joined__gte=month_start,
            date_joined__lt=month_end
        ).count()
        customer_growth.append({
            'month': month_start.strftime('%b %Y'),
            'new_customers': month_customers
        })
    
    # Customer segments (simplified since no user field in orders)
    segments = {
        'new': customers.count(),      # All customers are "new" since no order data
        'regular': 0,   # Can't calculate without user field
        'loyal': 0,    # Can't calculate without user field
        'vip': 0       # Can't calculate without user field
    }
    
    # Top customers by spending (empty since no user field)
    top_customers = []
    for customer in customers[:20]:
        # Since orders don't have user field, we can't calculate spending
        top_customers.append({
            'customer': customer,
            'total_spent': 0,
            'order_count': 0
        })
    
    # Customer retention (can't calculate without user field)
    retention_rate = 0
    
    context = {
        'customer_growth': customer_growth[::-1],  # Reverse to show chronological
        'segments': segments,
        'top_customers': top_customers[:10],
        'retention_rate': retention_rate,
        'total_customers': customers.count(),
    }
    return render(request, 'customer_analytics.html', context)

@login_required
@user_passes_test(is_admin)
def toggle_customer_status(request, customer_id):
    """Toggle customer active/inactive status"""
    if request.method == 'POST':
        customer = get_object_or_404(User, id=customer_id, is_staff=False)
        customer.is_active = not customer.is_active
        customer.save()
        
        status = 'activated' if customer.is_active else 'deactivated'
        return JsonResponse({
            'success': True,
            'message': f'Customer {status} successfully',
            'is_active': customer.is_active
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_admin)
def export_customers(request):
    """Export customer data as JSON"""
    customers = User.objects.filter(is_staff=False)
    
    customer_data = []
    for customer in customers:
        orders = Order.objects.filter(user=customer)
        total_spent = orders.aggregate(total=Sum('total_price'))['total'] or 0
        
        customer_data.append({
            'id': customer.id,
            'username': customer.username,
            'email': customer.email,
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'date_joined': customer.date_joined.isoformat(),
            'is_active': customer.is_active,
            'total_orders': orders.count(),
            'total_spent': float(total_spent),
            'last_login': customer.last_login.isoformat() if customer.last_login else None,
        })
    
    return JsonResponse({
        'customers': customer_data,
        'export_date': timezone.now().isoformat(),
        'total_count': len(customer_data)
    })
