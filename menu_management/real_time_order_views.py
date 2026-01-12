# -*- coding: utf-8 -*-
"""
Phase 2: Real-time Order Management and Customer Service Views
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
from decimal import Decimal
import json
import uuid

from .real_time_order_models import RealTimeOrderTracking, SpecialRequestManagement
from .customer_service_models import VIPCustomerManagement, CustomerFeedbackCollection
from .order_orchestration_models import UnifiedOrderQueue, OrderBatch, OrderPrioritization
from menu_management.models import VirtualBrand

def is_admin(user):
    return user.is_authenticated and user.is_staff

@login_required
@user_passes_test(is_admin)
def real_time_order_dashboard(request):
    """Real-time order management dashboard"""
    brand_id = request.GET.get('brand')
    
    # Get orders with real-time tracking
    orders = UnifiedOrderQueue.objects.select_related(
        'brand', 'real_time_tracking'
    ).prefetch_related('items').order_by('-order_time')
    
    if brand_id:
        orders = orders.filter(brand_id=brand_id)
    
    # Get brands for filter
    brands = VirtualBrand.objects.filter(is_active=True)
    
    # Calculate metrics
    total_orders = orders.count()
    active_orders = orders.filter(status__in=['received', 'confirmed', 'preparing']).count()
    completed_orders = orders.filter(status='completed').count()
    
    context = {
        'orders': orders,
        'brands': brands,
        'total_orders': total_orders,
        'active_orders': active_orders,
        'completed_orders': completed_orders,
        'selected_brand': brand_id,
    }
    
    return render(request, 'menu_management/real_time_order_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def update_order_status(request, order_id):
    """Update order status in real-time"""
    try:
        order = get_object_or_404(UnifiedOrderQueue, order_id=order_id)
        tracking = get_object_or_404(RealTimeOrderTracking, order=order)
        
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        # Update order status
        order.status = new_status
        order.save()
        
        # Update tracking
        tracking.current_status = new_status
        tracking.status_updated_at = timezone.now()
        
        # Update timing based on status
        if new_status == 'preparing':
            tracking.prep_started_at = timezone.now()
        elif new_status == 'ready':
            tracking.prep_completed_at = timezone.now()
            tracking.ready_at = timezone.now()
        elif new_status == 'completed':
            tracking.delivered_at = timezone.now()
        
        tracking.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Order status updated to {new_status}',
            'status': new_status,
            'updated_at': tracking.status_updated_at.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@user_passes_test(is_admin)
def special_requests_management(request):
    """Special requests management interface"""
    requests = SpecialRequestManagement.objects.select_related(
        'order', 'order__brand', 'assigned_to'
    ).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    # Get statistics
    total_requests = requests.count()
    pending_requests = requests.filter(status='pending').count()
    high_priority_requests = requests.filter(urgency='high').count()
    
    context = {
        'requests': requests,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'high_priority_requests': high_priority_requests,
        'status_filter': status_filter,
    }
    
    return render(request, 'menu_management/special_requests_management.html', context)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def handle_special_request(request, request_id):
    """Handle special request"""
    try:
        special_request = get_object_or_404(SpecialRequestManagement, request_id=request_id)
        
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        if action == 'acknowledge':
            special_request.status = 'acknowledged'
            special_request.kitchen_notified = True
        elif action == 'complete':
            special_request.status = 'completed'
            special_request.customer_informed = True
        elif action == 'reject':
            special_request.status = 'rejected'
        
        special_request.notes = notes
        special_request.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Request {action}d successfully',
            'status': special_request.status
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@user_passes_test(is_admin)
def vip_customer_management(request):
    """VIP customer management dashboard"""
    customers = VIPCustomerManagement.objects.all().order_by('-total_spent')
    
    # Filter by tier
    tier_filter = request.GET.get('tier')
    if tier_filter:
        customers = customers.filter(tier=tier_filter)
    
    # Get statistics
    total_customers = customers.count()
    gold_tier = customers.filter(tier='gold').count()
    platinum_tier = customers.filter(tier='platinum').count()
    
    context = {
        'customers': customers,
        'total_customers': total_customers,
        'gold_tier': gold_tier,
        'platinum_tier': platinum_tier,
        'tier_filter': tier_filter,
    }
    
    return render(request, 'menu_management/vip_customer_management.html', context)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def update_vip_customer(request, customer_id):
    """Update VIP customer information"""
    try:
        customer = get_object_or_404(VIPCustomerManagement, customer_id=customer_id)
        
        data = json.loads(request.body)
        
        # Update customer details
        if 'name' in data:
            customer.name = data['name']
        if 'email' in data:
            customer.email = data['email']
        if 'tier' in data:
            customer.tier = data['tier']
        if 'preferred_items' in data:
            customer.preferred_items = data['preferred_items']
        if 'special_instructions' in data:
            customer.special_instructions = data['special_instructions']
        
        # Update communication preferences
        if 'sms_notifications' in data:
            customer.sms_notifications = data['sms_notifications']
        if 'email_updates' in data:
            customer.email_updates = data['email_updates']
        
        customer.save()
        
        return JsonResponse({
            'success': True,
            'message': 'VIP customer updated successfully',
            'customer': {
                'name': customer.name,
                'tier': customer.tier,
                'total_orders': customer.total_orders,
                'total_spent': str(customer.total_spent)
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@user_passes_test(is_admin)
def customer_feedback_dashboard(request):
    """Customer feedback collection and analysis"""
    feedback = CustomerFeedbackCollection.objects.select_related(
        'order', 'order__brand'
    ).order_by('-created_at')
    
    # Filter by rating
    rating_filter = request.GET.get('rating')
    if rating_filter:
        feedback = feedback.filter(rating=int(rating_filter))
    
    # Calculate statistics
    total_feedback = feedback.count()
    average_rating = feedback.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
    five_star_reviews = feedback.filter(rating=5).count()
    
    # Feedback by type
    feedback_by_type = feedback.values('feedback_type').annotate(
        count=Count('id'),
        avg_rating=Avg('rating')
    ).order_by('-count')
    
    context = {
        'feedback': feedback,
        'total_feedback': total_feedback,
        'average_rating': round(average_rating, 1),
        'five_star_reviews': five_star_reviews,
        'feedback_by_type': feedback_by_type,
        'rating_filter': rating_filter,
    }
    
    return render(request, 'menu_management/customer_feedback_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def respond_to_feedback(request, feedback_id):
    """Respond to customer feedback"""
    try:
        feedback = get_object_or_404(CustomerFeedbackCollection, feedback_id=feedback_id)
        
        data = json.loads(request.body)
        response = data.get('response', '')
        follow_up = data.get('follow_up', False)
        
        # Mark as reviewed and responded
        feedback.reviewed = True
        feedback.response_sent = True
        feedback.follow_up_required = follow_up
        
        # Here you would typically send an email/SMS response
        # For now, we'll just mark it as sent
        
        feedback.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Response sent successfully',
            'follow_up_required': follow_up
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@user_passes_test(is_admin)
def order_prioritization_settings(request):
    """Order prioritization algorithm settings"""
    brand_id = request.GET.get('brand')
    
    if brand_id:
        brand = get_object_or_404(VirtualBrand, brand_id=brand_id)
        rules = OrderPrioritization.objects.filter(brand=brand, is_active=True).order_by('-priority')
    else:
        brand = None
        rules = OrderPrioritization.objects.filter(is_active=True).order_by('-priority')
    
    context = {
        'brand': brand,
        'rules': rules,
        'brands': VirtualBrand.objects.filter(is_active=True),
        'selected_brand': brand_id,
    }
    
    return render(request, 'menu_management/order_prioritization_settings.html', context)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def create_prioritization_rule(request):
    """Create new prioritization rule"""
    try:
        data = json.loads(request.body)
        
        brand = get_object_or_404(VirtualBrand, brand_id=data['brand_id'])
        
        rule = OrderPrioritization.objects.create(
            brand=brand,
            rule_type=data['rule_type'],
            weight=Decimal(str(data.get('weight', 1.0))),
            conditions=data.get('conditions', {}),
            priority=data.get('priority', 0)
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Prioritization rule created successfully',
            'rule_id': str(rule.rule_id)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@user_passes_test(is_admin)
def order_batching_dashboard(request):
    """Order batching and efficiency dashboard"""
    batches = OrderBatch.objects.select_related('brand').order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        batches = batches.filter(status=status_filter)
    
    # Calculate metrics
    total_batches = batches.count()
    active_batches = batches.filter(status='in_progress').count()
    avg_batch_size = batches.aggregate(avg_size=Avg('orders__count'))['avg_size'] or 0
    
    context = {
        'batches': batches,
        'total_batches': total_batches,
        'active_batches': active_batches,
        'avg_batch_size': round(avg_batch_size, 1),
        'status_filter': status_filter,
    }
    
    return render(request, 'menu_management/order_batching_dashboard.html', context)
