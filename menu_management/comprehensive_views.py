# -*- coding: utf-8 -*-
"""
Comprehensive Views for All Phases - POS Integration, Delivery Platforms, Order Management, etc.
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum, F
from django.core.paginator import Paginator
from decimal import Decimal
import json
import uuid

# Import all models from different phases
from .pos_integration_models import POSIntegration, POSOrder, POSMenuSync
from .delivery_integration_models import DeliveryPlatform, DeliveryOrder, PlatformPerformance
from .order_orchestration_models import UnifiedOrderQueue, UnifiedOrderBatch, OrderPrioritization
from .real_time_order_models import RealTimeOrderTracking, SpecialRequestManagement
from .customer_service_models import VIPCustomerManagement, CustomerFeedbackCollection
from .advanced_scheduling_models import LaborLawCompliance, ScheduleOptimization, ForecastedLaborRequirements
from .kitchen_optimization_models import KitchenLayoutOptimization, PackagingManagement, TemperatureMonitoring
from .multi_location_models import CloudKitchenLocation, LocationPerformanceMetrics, CentralPrepKitchen

def is_admin(user):
    return user.is_authenticated and user.is_staff

# ============================================
# PHASE 1: POS and Delivery Platform Integration
# ============================================

@login_required
@user_passes_test(is_admin)
def pos_integration_dashboard(request):
    """POS Integration Dashboard"""
    integrations = POSIntegration.objects.select_related('restaurant').order_by('-created_at')
    
    # Get statistics
    total_integrations = integrations.count()
    active_integrations = integrations.filter(is_active=True).count()
    
    # Recent sync activity
    recent_syncs = POSMenuSync.objects.select_related('pos_integration').order_by('-sync_time')[:10]
    
    context = {
        'integrations': integrations,
        'total_integrations': total_integrations,
        'active_integrations': active_integrations,
        'recent_syncs': recent_syncs,
    }
    
    return render(request, 'menu_management/pos_integration_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def setup_pos_integration(request):
    """Setup POS integration"""
    try:
        data = json.loads(request.body)
        
        brand_id = data['brand_id']
        pos_system = data['pos_system']
        api_key = data.get('api_key', '')
        api_secret = data.get('api_secret', '')
        
        brand = get_object_or_404(VirtualBrand, brand_id=brand_id)
        
        integration = POSIntegration.objects.create(
            restaurant=brand,
            pos_system=pos_system,
            api_key=api_key,
            api_secret=api_secret,
            is_active=True,
            auto_sync=True
        )
        
        return JsonResponse({
            'success': True,
            'message': 'POS integration setup successfully',
            'integration_id': str(integration.id)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@user_passes_test(is_admin)
def delivery_platform_dashboard(request):
    """Delivery Platform Integration Dashboard"""
    platforms = DeliveryPlatform.objects.select_related('restaurant').order_by('-created_at')
    
    # Get statistics
    total_platforms = platforms.count()
    active_platforms = platforms.filter(is_active=True).count()
    
    # Performance data
    performance_data = PlatformPerformance.objects.filter(
        date=timezone.now().date()
    ).select_related('platform')
    
    # Recent orders
    recent_orders = DeliveryOrder.objects.select_related('platform').order_by('-order_time')[:10]
    
    context = {
        'platforms': platforms,
        'total_platforms': total_platforms,
        'active_platforms': active_platforms,
        'performance_data': performance_data,
        'recent_orders': recent_orders,
    }
    
    return render(request, 'menu_management/delivery_platform_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def setup_delivery_platform(request):
    """Setup delivery platform integration"""
    try:
        data = json.loads(request.body)
        
        brand_id = data['brand_id']
        platform = data['platform']
        client_id = data.get('client_id', '')
        client_secret = data.get('client_secret', '')
        
        brand = get_object_or_404(VirtualBrand, brand_id=brand_id)
        
        delivery_platform = DeliveryPlatform.objects.create(
            restaurant=brand,
            platform=platform,
            client_id=client_id,
            client_secret=client_secret,
            is_active=True,
            auto_accept_orders=True,
            auto_sync_orders=True
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Delivery platform setup successfully',
            'platform_id': str(delivery_platform.id)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

# ============================================
# PHASE 2: Real-time Order Management
# ============================================

@login_required
@user_passes_test(is_admin)
def unified_order_queue(request):
    """Unified order queue across all platforms and brands"""
    orders = UnifiedOrderQueue.objects.select_related(
        'brand', 'real_time_tracking', 'kitchen_order'
    ).order_by('-order_time')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Filter by brand
    brand_filter = request.GET.get('brand')
    if brand_filter:
        orders = orders.filter(brand_id=brand_filter)
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get brands for filter
    brands = VirtualBrand.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'brands': brands,
        'status_filter': status_filter,
        'brand_filter': brand_filter,
    }
    
    return render(request, 'menu_management/unified_order_queue.html', context)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def create_order_batch(request):
    """Create order batch for kitchen efficiency"""
    try:
        data = json.loads(request.body)
        
        brand_id = data['brand_id']
        station = data['station']
        batch_type = data.get('batch_type', 'prep')
        order_ids = data.get('order_ids', [])
        
        brand = get_object_or_404(VirtualBrand, brand_id=brand_id)
        
        # Create batch
        batch = UnifiedOrderBatch.objects.create(
            brand=brand,
            station=station,
            batch_type=batch_type
        )
        
        # Add orders to batch
        orders = UnifiedOrderQueue.objects.filter(order_id__in=order_ids)
        batch.orders.add(*orders)
        
        # Calculate batch metrics
        batch.total_items = orders.aggregate(total=Sum('items__length'))['total'] or 0
        batch.total_value = orders.aggregate(total=Sum('total'))['total'] or Decimal('0')
        
        return JsonResponse({
            'success': True,
            'message': 'Order batch created successfully',
            'batch_id': str(batch.batch_id),
            'total_orders': orders.count()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

# ============================================
# PHASE 3: Advanced Scheduling and Kitchen Optimization
# ============================================

@login_required
@user_passes_test(is_admin)
def advanced_scheduling_dashboard(request):
    """Advanced scheduling dashboard"""
    # Get scheduling data
    optimizations = ScheduleOptimization.objects.select_related('brand').order_by('-created_at')
    
    # Get compliance data
    compliance_issues = LaborLawCompliance.objects.filter(is_active=True)
    
    # Get forecasts
    forecasts = ForecastedLaborRequirements.objects.filter(
        forecast_date__gte=timezone.now().date()
    ).order_by('forecast_date')[:7]
    
    context = {
        'optimizations': optimizations,
        'compliance_issues': compliance_issues,
        'forecasts': forecasts,
    }
    
    return render(request, 'menu_management/advanced_scheduling_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def create_schedule_optimization(request):
    """Create schedule optimization"""
    try:
        data = json.loads(request.body)
        
        brand_id = data['brand_id']
        target_date = data['target_date']
        optimization_type = data['optimization_type']
        target_labor_cost = Decimal(str(data.get('target_labor_cost', 0)))
        
        brand = get_object_or_404(VirtualBrand, brand_id=brand_id)
        
        optimization = ScheduleOptimization.objects.create(
            brand=brand,
            target_date=target_date,
            optimization_type=optimization_type,
            target_labor_cost=target_labor_cost
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Schedule optimization created successfully',
            'optimization_id': str(optimization.optimization_id)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@user_passes_test(is_admin)
def kitchen_layout_designer(request):
    """Kitchen layout designer and optimization"""
    layouts = KitchenLayoutOptimization.objects.select_related('brand').order_by('-created_at')
    
    # Get active layout
    active_layout = layouts.filter(is_active=True).first()
    
    context = {
        'layouts': layouts,
        'active_layout': active_layout,
    }
    
    return render(request, 'menu_management/kitchen_layout_designer.html', context)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def save_kitchen_layout(request):
    """Save kitchen layout design"""
    try:
        data = json.loads(request.body)
        
        layout_id = data.get('layout_id')
        layout_name = data['layout_name']
        brand_id = data['brand_id']
        dimensions = data['dimensions']
        stations = data['stations']
        equipment = data['equipment']
        workflow_paths = data['workflow_paths']
        
        brand = get_object_or_404(VirtualBrand, brand_id=brand_id)
        
        if layout_id:
            # Update existing layout
            layout = get_object_or_404(KitchenLayoutOptimization, layout_id=layout_id)
            layout.layout_name = layout_name
            layout.dimensions = dimensions
            layout.stations = stations
            layout.equipment = equipment
            layout.workflow_paths = workflow_paths
        else:
            # Create new layout
            layout = KitchenLayoutOptimization.objects.create(
                brand=brand,
                layout_name=layout_name,
                layout_type='proposed',
                dimensions=dimensions,
                stations=stations,
                equipment=equipment,
                workflow_paths=workflow_paths
            )
        
        layout.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Kitchen layout saved successfully',
            'layout_id': str(layout.layout_id)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@user_passes_test(is_admin)
def packaging_management_dashboard(request):
    """Packaging management dashboard"""
    packaging = PackagingManagement.objects.select_related('brand').order_by('-created_at')
    
    # Get cost tracking data
    cost_tracking = PackagingCostTracking.objects.select_related('brand').order_by('-created_at')[:20]
    
    # Get temperature monitoring data
    temp_monitoring = TemperatureMonitoring.objects.select_related('package_type').order_by('-test_date')[:10]
    
    context = {
        'packaging': packaging,
        'cost_tracking': cost_tracking,
        'temp_monitoring': temp_monitoring,
    }
    
    return render(request, 'menu_management/packaging_management_dashboard.html', context)

# ============================================
# PHASE 4: Multi-Location Cloud Kitchen Network
# ============================================

@login_required
@user_passes_test(is_admin)
def multi_location_dashboard(request):
    """Multi-location cloud kitchen network dashboard"""
    locations = CloudKitchenLocation.objects.all().order_by('-created_at')
    
    # Get performance metrics
    performance_data = LocationPerformanceMetrics.objects.filter(
        date=timezone.now().date()
    ).select_related('location')
    
    # Get inventory transfers
    transfers = InterLocationInventoryTransfer.objects.select_related(
        'source_location', 'destination_location'
    ).order_by('-created_at')[:10]
    
    context = {
        'locations': locations,
        'performance_data': performance_data,
        'transfers': transfers,
    }
    
    return render(request, 'menu_management/multi_location_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def create_cloud_kitchen_location(request):
    """Create new cloud kitchen location"""
    try:
        data = json.loads(request.body)
        
        name = data['name']
        code = data['code']
        kitchen_type = data['kitchen_type']
        address = data['address']
        city = data['city']
        state = data['state']
        country = data['country']
        postal_code = data['postal_code']
        latitude = Decimal(str(data['latitude']))
        longitude = Decimal(str(data['longitude']))
        
        location = CloudKitchenLocation.objects.create(
            name=name,
            code=code,
            kitchen_type=kitchen_type,
            address=address,
            city=city,
            state=state,
            country=country,
            postal_code=postal_code,
            latitude=latitude,
            longitude=longitude
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Cloud kitchen location created successfully',
            'location_id': str(location.location_id)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@user_passes_test(is_admin)
def hub_and_spoke_operations(request):
    """Hub-and-spoke operations dashboard"""
    central_kitchens = CentralPrepKitchen.objects.all().order_by('-created_at')
    
    # Get processing schedules
    processing_schedules = BulkIngredientProcessing.objects.select_related('central_kitchen').order_by('-processing_date')[:10]
    
    # Get logistics routes
    logistics_routes = InterLocationLogistics.objects.filter(is_active=True).order_by('-created_at')
    
    context = {
        'central_kitchens': central_kitchens,
        'processing_schedules': processing_schedules,
        'logistics_routes': logistics_routes,
    }
    
    return render(request, 'menu_management/hub_and_spoke_operations.html', context)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def create_central_prep_kitchen(request):
    """Create central prep kitchen"""
    try:
        data = json.loads(request.body)
        
        name = data['name']
        code = data['code']
        kitchen_type = data['kitchen_type']
        address = data['address']
        city = data['city']
        state = data['state']
        coordinates = data['coordinates']
        
        kitchen = CentralPrepKitchen.objects.create(
            name=name,
            code=code,
            kitchen_type=kitchen_type,
            address=address,
            city=city,
            state=state,
            coordinates=coordinates
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Central prep kitchen created successfully',
            'kitchen_id': str(kitchen.kitchen_id)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

# ============================================
# Unified Management Dashboard
# ============================================

@login_required
@user_passes_test(is_admin)
def comprehensive_management_dashboard(request):
    """Comprehensive management dashboard for all phases"""
    # Phase 1 metrics
    pos_integrations = POSIntegration.objects.filter(is_active=True).count()
    delivery_platforms = DeliveryPlatform.objects.filter(is_active=True).count()
    
    # Phase 2 metrics
    active_orders = UnifiedOrderQueue.objects.filter(status__in=['received', 'confirmed', 'preparing']).count()
    completed_orders = UnifiedOrderQueue.objects.filter(status='completed').count()
    
    # Phase 3 metrics
    schedule_optimizations = ScheduleOptimization.objects.filter(applied=True).count()
    kitchen_layouts = KitchenLayoutOptimization.objects.filter(is_active=True).count()
    
    # Phase 4 metrics
    cloud_kitchens = CloudKitchenLocation.objects.filter(is_active=True).count()
    central_kitchens = CentralPrepKitchen.objects.all().count()
    
    # Recent activity
    recent_orders = UnifiedOrderQueue.objects.select_related('brand').order_by('-order_time')[:5]
    recent_syncs = POSMenuSync.objects.select_related('pos_integration').order_by('-sync_time')[:5]
    
    context = {
        # Phase 1
        'pos_integrations': pos_integrations,
        'delivery_platforms': delivery_platforms,
        
        # Phase 2
        'active_orders': active_orders,
        'completed_orders': completed_orders,
        
        # Phase 3
        'schedule_optimizations': schedule_optimizations,
        'kitchen_layouts': kitchen_layouts,
        
        # Phase 4
        'cloud_kitchens': cloud_kitchens,
        'central_kitchens': central_kitchens,
        
        # Activity
        'recent_orders': recent_orders,
        'recent_syncs': recent_syncs,
    }
    
    return render(request, 'menu_management/comprehensive_management_dashboard.html', context)

# ============================================
# API Endpoints for Real-time Updates
# ============================================

@login_required
@user_passes_test(is_admin)
def get_real_time_metrics(request):
    """Get real-time metrics for dashboard"""
    try:
        # Order metrics
        active_orders = UnifiedOrderQueue.objects.filter(status__in=['received', 'confirmed', 'preparing']).count()
        completed_today = UnifiedOrderQueue.objects.filter(
            status='completed',
            completed_time__date=timezone.now().date()
        ).count()
        
        # Revenue metrics
        today_revenue = UnifiedOrderQueue.objects.filter(
            order_time__date=timezone.now().date()
        ).aggregate(total=Sum('total'))['total'] or Decimal('0')
        
        # Platform metrics
        active_platforms = DeliveryPlatform.objects.filter(is_active=True).count()
        
        # Location metrics
        active_kitchens = CloudKitchenLocation.objects.filter(is_active=True).count()
        
        return JsonResponse({
            'success': True,
            'metrics': {
                'active_orders': active_orders,
                'completed_today': completed_today,
                'today_revenue': float(today_revenue),
                'active_platforms': active_platforms,
                'active_kitchens': active_kitchens,
                'timestamp': timezone.now().isoformat()
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@user_passes_test(is_admin)
def get_order_queue_status(request):
    """Get current order queue status"""
    try:
        orders = UnifiedOrderQueue.objects.select_related('brand', 'real_time_tracking').order_by('-order_time')[:10]
        
        order_data = []
        for order in orders:
            order_data.append({
                'order_id': str(order.order_id),
                'brand_name': order.brand.name,
                'status': order.status,
                'priority': order.priority,
                'order_time': order.order_time.isoformat(),
                'promised_time': order.promised_time.isoformat() if order.promised_time else None,
                'estimated_completion': order.real_time_tracking.estimated_completion.isoformat() if order.real_time_tracking.estimated_completion else None,
                'progress_percentage': order.real_time_tracking.progress_percentage,
                'current_step': order.real_time_tracking.current_step,
            })
        
        return JsonResponse({
            'success': True,
            'orders': order_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
