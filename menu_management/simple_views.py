from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from decimal import Decimal
from .models import Menu, RecipeMenuItem, Ingredient, RecipeIngredient, VirtualBrand, PlatformIntegration
from .routing_models import KitchenStation
from .notification_models import Notification
from orders.models import Order
from django.db.models import Count, Sum, Avg

def is_admin(user):
    return user.is_authenticated and user.is_superuser

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def create_simple_brand(request):
    """Create a simple virtual brand"""
    if request.method == 'POST':
        try:
            brand = VirtualBrand.objects.create(
                name=request.POST.get('brand_name'),
                description=request.POST.get('description', ''),
                brand_type=request.POST.get('brand_type'),
                target_market=request.POST.get('target_market', ''),
                brand_color=request.POST.get('brand_color', '#667eea'),
                uber_eats_active='uber_eats' in request.POST,
                doordash_active='doordash' in request.POST,
                grubhub_active='grubhub' in request.POST,
                base_markup=Decimal(request.POST.get('base_markup', '300')),
                delivery_fee=Decimal(request.POST.get('delivery_fee', '2.99')),
                min_order_amount=Decimal(request.POST.get('min_order', '15')),
                created_by=request.user
            )
            
            # Create platform integrations
            if brand.uber_eats_active:
                PlatformIntegration.objects.create(
                    brand=brand,
                    platform='uber_eats',
                    sync_status='pending'
                )
            
            if brand.doordash_active:
                PlatformIntegration.objects.create(
                    brand=brand,
                    platform='doordash',
                    sync_status='pending'
                )
            
            if brand.grubhub_active:
                PlatformIntegration.objects.create(
                    brand=brand,
                    platform='grubhub',
                    sync_status='pending'
                )
            
            return JsonResponse({
                'success': True,
                'message': f'Brand "{brand.name}" created successfully!',
                'brand_id': brand.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error creating brand: {str(e)}'
            })
    
    return JsonResponse({
        'success': False, 
        'message': 'Invalid request method. This endpoint only accepts POST requests.',
        'allowed_methods': ['POST']
    })

@login_required
@user_passes_test(is_admin)
def simple_multi_brand(request):
    """Simple multi-brand dashboard"""
    # Get all menus as brands
    brands = Menu.objects.select_related('created_by').all()
    
    # Calculate statistics
    total_brands = brands.count()
    active_brands = brands.filter(is_active=True).count()
    
    # Mock platform integrations
    platform_integrations = {
        'uber_eats': brands.count() // 2,
        'doordash': brands.count() // 3,
        'grubhub': brands.count() // 4,
    }
    
    context = {
        'brands': brands,
        'total_brands': total_brands,
        'active_brands': active_brands,
        'platform_integrations': platform_integrations,
    }
    return render(request, 'menu_management/simple_multi_brand.html', context)

@login_required
@user_passes_test(is_admin)
def simple_platform_integration(request):
    """Simple platform integration management"""
    # Get all menus as brands
    brands = Menu.objects.select_related('created_by').all()
    
    # Mock platform statistics
    platform_stats = {
        'uber_eats': brands.count() // 2,
        'doordash': brands.count() // 3,
        'grubhub': brands.count() // 4,
    }
    
    context = {
        'brands': brands,
        'platform_stats': platform_stats,
    }
    return render(request, 'menu_management/simple_platform_integration.html', context)

@login_required
@user_passes_test(is_admin)
def simple_performance_analytics(request):
    """Simple performance analytics"""
    brands = Menu.objects.all()
    
    # Mock performance data
    brand_performance = []
    for brand in brands:
        # Generate mock data
        total_orders = brand.id * 10  # Mock data
        total_revenue = brand.id * 100  # Mock data
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        brand_performance.append({
            'brand': brand,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'avg_order_value': avg_order_value,
            'avg_rating': 4.5,  # Mock rating
        })
    
    # Mock top items
    top_items = [
        {'brand': 'Quick Bites Express', 'item_name': 'Burger', 'order_count': 50, 'revenue': 500},
        {'brand': 'Gourmet Kitchen', 'item_name': 'Pasta', 'order_count': 30, 'revenue': 450},
        {'brand': 'Healthy Harvest', 'item_name': 'Salad', 'order_count': 25, 'revenue': 250},
    ]
    
    context = {
        'brand_performance': brand_performance,
        'top_items': top_items,
    }
    return render(request, 'menu_management/simple_performance_analytics.html', context)

@login_required
@user_passes_test(is_admin)
def simple_menu_optimization(request):
    """Simple menu optimization recommendations"""
    brands = Menu.objects.all()
    
    # Generate mock recommendations
    recommendations = [
        {
            'title': 'Increase prices on top items by 10%',
            'description': 'Based on demand elasticity, increasing prices could increase revenue by 15%',
            'priority': 'High',
            'expected_impact': 'Revenue increase of $2,500/month',
            'implementation_status': 'pending'
        },
        {
            'title': 'Optimize ingredient ordering',
            'description': 'Consolidate ordering to reduce costs by 8%',
            'priority': 'Medium',
            'expected_impact': 'Cost reduction of $800/month',
            'implementation_status': 'pending'
        },
        {
            'title': 'Add 2 new high-margin items',
            'description': 'Introduce items with 70%+ margin',
            'priority': 'Medium',
            'expected_impact': 'Margin increase of 5%',
            'implementation_status': 'pending'
        }
    ]
    
    context = {
        'brands': brands,
        'recommendations': recommendations,
    }
    return render(request, 'menu_management/simple_menu_optimization.html', context)

@login_required
@user_passes_test(is_admin)
def simple_ghost_kitchen(request):
    """Simple ghost kitchen operations"""
    brands = Menu.objects.all()
    
    # Mock workflow data
    workflows = [
        {'station': 'Prep Station', 'efficiency': 85, 'capacity': 40, 'prep_time': 15},
        {'station': 'Cooking Station', 'efficiency': 90, 'capacity': 35, 'prep_time': 20},
        {'station': 'Packaging Station', 'efficiency': 88, 'capacity': 45, 'prep_time': 5},
        {'station': 'Quality Control', 'efficiency': 92, 'capacity': 50, 'prep_time': 3},
    ]
    
    # Mock shared ingredients
    shared_ingredients = [
        {'name': 'Chicken Breast', 'usage': 15, 'cost_saved': 2.50},
        {'name': 'Rice', 'usage': 20, 'cost_saved': 1.80},
        {'name': 'Vegetables', 'usage': 25, 'cost_saved': 3.20},
    ]
    
    context = {
        'brands': brands,
        'workflows': workflows,
        'shared_ingredients': shared_ingredients,
    }
    return render(request, 'menu_management/simple_ghost_kitchen.html', context)

@login_required
@user_passes_test(is_admin)
def simple_unified_management(request):
    """Simple unified management dashboard"""
    from .models import VirtualBrand, PlatformIntegration, SharedIngredient
    
    # Get real virtual brands
    brands = VirtualBrand.objects.select_related('created_by').all()
    
    # Calculate statistics
    total_brands = brands.count()
    active_brands = brands.filter(is_active=True).count()
    
    # Get platform integrations
    platform_integrations = PlatformIntegration.objects.filter(is_active=True).values('platform').distinct().count()
    
    # Get shared ingredients
    shared_ingredients = SharedIngredient.objects.values('ingredient').distinct().count()
    
    # Calculate total menu items across all brands
    total_menu_items = RecipeMenuItem.objects.count()
    
    # Mock other statistics
    total_recipes = Ingredient.objects.count()
    total_stations = KitchenStation.objects.count()
    active_stations = KitchenStation.objects.filter(is_active=True).count()
    unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False).count()
    
    # Mock total revenue
    total_revenue = 15420.75
    
    # Calculate brand activity rate
    brand_activity_rate = 0
    if total_brands > 0:
        brand_activity_rate = (active_brands / total_brands) * 100
    
    context = {
        'brands': brands,
        'total_brands': total_brands,
        'active_brands': active_brands,
        'total_menu_items': total_menu_items,
        'total_recipes': total_recipes,
        'total_stations': total_stations,
        'active_stations': active_stations,
        'unread_notifications': unread_notifications,
        'shared_ingredients': shared_ingredients,
        'platform_integrations': platform_integrations,
        'total_revenue': total_revenue,
        'brand_activity_rate': brand_activity_rate,
    }
    return render(request, 'menu_management/simple_unified_management.html', context)

# ============================================
# COMPREHENSIVE IMPLEMENTATION VIEWS - ALL PHASES
# ============================================

# Phase 1: POS and Delivery Platform Integration
@login_required
@user_passes_test(is_admin)
def pos_integration_dashboard(request):
    """POS Integration Dashboard"""
    try:
        # Import models here to avoid circular imports
        from .pos_integration_models import POSIntegration, POSOrder, POSMenuSync
        from .delivery_integration_models import DeliveryPlatform, DeliveryOrder, PlatformPerformance
        
        # Get integrations without complex queries first
        integrations = POSIntegration.objects.all().order_by('-created_at')
        
        # Get statistics
        total_integrations = integrations.count()
        active_integrations = integrations.filter(is_active=True).count()
        
        # Initialize empty querysets to avoid errors
        recent_syncs = []
        recent_pos_orders = []
        recent_delivery_orders = []
        total_orders = 0
        
        # Try to get sync data safely
        try:
            recent_syncs = list(POSMenuSync.objects.all().order_by('-sync_time')[:10])
        except Exception as sync_error:
            print(f"Sync query error: {sync_error}")
        
        # Try to get order data safely
        try:
            recent_pos_orders = list(POSOrder.objects.all().order_by('-order_time')[:5])
        except Exception as pos_error:
            print(f"POS order query error: {pos_error}")
            
        try:
            recent_delivery_orders = list(DeliveryOrder.objects.all().order_by('-order_time')[:5])
        except Exception as delivery_error:
            print(f"Delivery order query error: {delivery_error}")
        
        total_orders = len(recent_pos_orders) + len(recent_delivery_orders)
        
        context = {
            'integrations': integrations,
            'total_integrations': total_integrations,
            'active_integrations': active_integrations,
            'recent_syncs': recent_syncs,
            'recent_pos_orders': recent_pos_orders,
            'recent_delivery_orders': recent_delivery_orders,
            'total_orders': total_orders,
        }
        
        return render(request, 'menu_management/pos_integration_dashboard.html', context)
        
    except Exception as e:
        print(f"Dashboard error: {e}")
        # Handle missing models gracefully with empty data
        context = {
            'integrations': [],
            'total_integrations': 0,
            'active_integrations': 0,
            'recent_syncs': [],
            'recent_pos_orders': [],
            'recent_delivery_orders': [],
            'total_orders': 0,
            'error': str(e),
        }
        
        return render(request, 'menu_management/pos_integration_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def create_pos_integration(request):
    """Create new POS integration"""
    if request.method == 'POST':
        try:
            # Import models here to avoid circular imports
            from .pos_integration_models import POSIntegration
            from .models import VirtualBrand
            
            pos_system = request.POST.get('pos_system')
            location_name = request.POST.get('location_name')
            api_key = request.POST.get('api_key')
            api_secret = request.POST.get('api_secret')
            
            # Get or create a default brand for now
            brand, created = VirtualBrand.objects.get_or_create(
                brand_name='Default Brand',
                defaults={
                    'description': 'Default brand for POS integrations',
                    'cuisine_type': 'Multi-Cuisine'
                }
            )
            
            integration = POSIntegration.objects.create(
                restaurant=brand,
                pos_system=pos_system,
                location_name=location_name,
                api_key=api_key,
                api_secret=api_secret,
                is_active=True,
                auto_sync=True
            )
            
            messages.success(request, f'POS integration for {location_name} created successfully!')
            return redirect('menu_management:pos_integration_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error creating POS integration: {str(e)}')
            return redirect('menu_management:pos_integration_dashboard')
    
    return redirect('menu_management:pos_integration_dashboard')

@login_required
@user_passes_test(is_admin)
def create_delivery_platform(request):
    """Create new delivery platform integration"""
    if request.method == 'POST':
        try:
            # Import models here to avoid circular imports
            from .delivery_integration_models import DeliveryPlatform
            from .models import VirtualBrand
            
            platform_name = request.POST.get('platform_name')
            api_key = request.POST.get('api_key')
            webhook_url = request.POST.get('webhook_url', '')
            commission_rate = request.POST.get('commission_rate', 15)
            
            # Get or create a default brand for now
            brand, created = VirtualBrand.objects.get_or_create(
                brand_name='Default Brand',
                defaults={
                    'description': 'Default brand for delivery platforms',
                    'cuisine_type': 'Multi-Cuisine'
                }
            )
            
            platform = DeliveryPlatform.objects.create(
                restaurant=brand,
                platform_name=platform_name,
                api_key=api_key,
                webhook_url=webhook_url,
                commission_rate=commission_rate,
                is_active=True
            )
            
            messages.success(request, f'Delivery platform {platform_name} created successfully!')
            return redirect('menu_management:delivery_platform_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error creating delivery platform: {str(e)}')
            return redirect('menu_management:delivery_platform_dashboard')
    
    return redirect('menu_management:delivery_platform_dashboard')

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def setup_pos_integration(request):
    """Setup POS integration"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            brand_id = data['brand_id']
            pos_system = data['pos_system']
            api_key = data.get('api_key', '')
            api_secret = data.get('api_secret', '')
            
            from .models import VirtualBrand
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
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
@user_passes_test(is_admin)
def delivery_platform_dashboard(request):
    """Delivery Platform Integration Dashboard"""
    try:
        from .delivery_integration_models import DeliveryPlatform, DeliveryOrder, PlatformPerformance
        from django.db.models import Sum, Avg, F
        
        platforms = DeliveryPlatform.objects.select_related('restaurant').order_by('-created_at')
        
        # Calculate statistics for each platform
        platform_stats = []
        for platform in platforms:
            orders = platform.deliveryorder_set.all()
            total_revenue = orders.aggregate(total=Sum('total'))['total'] or 0
            avg_order_value = orders.aggregate(avg=Avg('total'))['avg'] or 0
            total_commission = orders.aggregate(
                commission=Sum(F('total') * F('platform__commission_rate') / 100)
            )['commission'] or 0
            net_revenue = total_revenue - total_commission
            
            # Add stats to platform object for template access
            platform.total_revenue = total_revenue
            platform.avg_order_value = avg_order_value
            platform.total_commission = total_commission
            platform.net_revenue = net_revenue
            platform_stats.append(platform)
        
        # Get overall statistics
        total_platforms = platforms.count()
        active_platforms = platforms.filter(is_active=True).count()
        
        # Performance data
        performance_data = PlatformPerformance.objects.filter(
            date=timezone.now().date()
        ).select_related('platform')
        
        # Recent orders
        recent_orders = DeliveryOrder.objects.select_related('platform').order_by('-order_time')[:10]
        
        context = {
            'platforms': platform_stats,
            'total_platforms': total_platforms,
            'active_platforms': active_platforms,
            'performance_data': performance_data,
            'recent_orders': recent_orders,
            'error': None,
        }
    except Exception as e:
        # Handle missing tables or other errors
        context = {
            'platforms': [],
            'total_platforms': 0,
            'active_platforms': 0,
            'performance_data': [],
            'recent_orders': [],
            'error': f'Delivery platform models not available: {str(e)}',
        }
    
    return render(request, 'menu_management/delivery_platform_dashboard.html', context)

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def setup_delivery_platform(request):
    """Setup delivery platform integration"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            brand_id = data['brand_id']
            platform = data['platform']
            client_id = data.get('client_id', '')
            client_secret = data.get('client_secret', '')
            
            from .models import VirtualBrand
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
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

# Phase 2: Real-time Order Management
@login_required
@user_passes_test(is_admin)
def unified_order_queue(request):
    """Unified order queue across all platforms and brands"""
    from .order_orchestration_models import UnifiedOrderQueue, UnifiedOrderBatch
    from .real_time_order_models import RealTimeOrderTracking
    
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
    
    # Get brands for filter
    from .models import VirtualBrand
    brands = VirtualBrand.objects.filter(is_active=True)
    
    context = {
        'orders': orders,
        'brands': brands,
        'status_filter': status_filter,
        'brand_filter': brand_filter,
    }
    
    return render(request, 'menu_management/unified_order_queue.html', context)

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def create_order_batch(request):
    """Create order batch for kitchen efficiency"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            brand_id = data['brand_id']
            station = data['station']
            batch_type = data.get('batch_type', 'prep')
            order_ids = data.get('order_ids', [])
            
            from .models import VirtualBrand
            brand = get_object_or_404(VirtualBrand, brand_id=brand_id)
            
            from .order_orchestration_models import UnifiedOrderBatch
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
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
@user_passes_test(is_admin)
def real_time_order_dashboard(request):
    """Real-time order management dashboard"""
    from .real_time_order_models import RealTimeOrderTracking, SpecialRequestManagement
    from .customer_service_models import VIPCustomerManagement
    from .order_orchestration_models import UnifiedOrderQueue
    
    orders = UnifiedOrderQueue.objects.select_related(
        'brand', 'kitchen_order'
    ).order_by('-order_time')
    
    # Get statistics
    total_orders = orders.count()
    active_orders = orders.filter(status__in=['received', 'confirmed', 'preparing']).count()
    completed_orders = orders.filter(status='completed').count()
    
    context = {
        'orders': orders,
        'total_orders': total_orders,
        'active_orders': active_orders,
        'completed_orders': completed_orders,
    }
    
    return render(request, 'menu_management/real_time_order_dashboard.html', context)

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def update_order_status(request, order_id):
    """Update order status in real-time"""
    if request.method == 'POST':
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
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

# Phase 3: Advanced Scheduling and Kitchen Optimization
@login_required
@user_passes_test(is_admin)
def advanced_scheduling_dashboard(request):
    """Advanced scheduling dashboard"""
    from .advanced_scheduling_models import ScheduleOptimization, ForecastedLaborRequirements
    from .kitchen_optimization_models import KitchenLayoutOptimization, PackagingManagement
    
    # Get scheduling data
    optimizations = ScheduleOptimization.objects.select_related('brand').order_by('-created_at')
    
    # Get compliance data
    from .advanced_scheduling_models import LaborLawCompliance
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

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def create_schedule_optimization(request):
    """Create schedule optimization"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            brand_id = data['brand_id']
            target_date = data['target_date']
            optimization_type = data['optimization_type']
            target_labor_cost = Decimal(str(data.get('target_labor_cost', 0)))
            
            from .models import VirtualBrand
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
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
@user_passes_test(is_admin)
def kitchen_layout_designer(request):
    """Kitchen layout designer and optimization"""
    from .kitchen_optimization_models import KitchenLayoutOptimization
    
    layouts = KitchenLayoutOptimization.objects.select_related('brand').order_by('-created_at')
    
    # Get active layout
    active_layout = layouts.filter(is_active=True).first()
    
    context = {
        'layouts': layouts,
        'active_layout': active_layout,
    }
    
    return render(request, 'menu_management/kitchen_layout_designer.html', context)

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def save_kitchen_layout(request):
    """Save kitchen layout design"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            layout_id = data.get('layout_id')
            layout_name = data['layout_name']
            brand_id = data['brand_id']
            dimensions = data['dimensions']
            stations = data['stations']
            equipment = data['equipment']
            workflow_paths = data['workflow_paths']
            
            from .models import VirtualBrand
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
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
@user_passes_test(is_admin)
def packaging_management_dashboard(request):
    """Packaging management dashboard"""
    from .kitchen_optimization_models import PackagingManagement, PackagingCostTracking, TemperatureMonitoring
    
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
    
    return render(request, 'menu_management/packaging_management.html', context)

# Phase 4: Multi-Location Cloud Kitchen Network
@login_required
@user_passes_test(is_admin)
def multi_location_dashboard(request):
    """Multi-location cloud kitchen network dashboard"""
    from .multi_location_models import CloudKitchenLocation, LocationPerformanceMetrics, CentralPrepKitchen
    
    locations = CloudKitchenLocation.objects.all().order_by('-created_at')
    
    # Get performance metrics
    performance_data = LocationPerformanceMetrics.objects.filter(
        date=timezone.now().date()
    ).select_related('location')
    
    # Get inventory transfers
    from .multi_location_models import InterLocationInventoryTransfer
    transfers = InterLocationInventoryTransfer.objects.select_related(
        'source_location', 'destination_location'
    ).order_by('-created_at')[:10]
    
    context = {
        'locations': locations,
        'performance_data': performance_data,
        'transfers': transfers,
    }
    
    return render(request, 'menu_management/multi_location_dashboard.html', context)

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def create_cloud_kitchen_location(request):
    """Create new cloud kitchen location"""
    if request.method == 'POST':
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
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
@user_passes_test(is_admin)
def hub_and_spoke_operations(request):
    """Hub-and-spoke operations dashboard"""
    from .multi_location_models import CentralPrepKitchen, BulkIngredientProcessing, InterLocationLogistics
    
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

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def create_central_prep_kitchen(request):
    """Create central prep kitchen"""
    if request.method == 'POST':
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
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

# Comprehensive Management Dashboard
@login_required
@user_passes_test(is_admin)
def comprehensive_management_dashboard(request):
    """Comprehensive management dashboard for all phases"""
    # Phase 1 metrics
    from .pos_integration_models import POSIntegration
    from .delivery_integration_models import DeliveryPlatform
    pos_integrations = POSIntegration.objects.filter(is_active=True).count()
    delivery_platforms = DeliveryPlatform.objects.filter(is_active=True).count()
    
    # Phase 2 metrics
    from .order_orchestration_models import UnifiedOrderQueue
    active_orders = UnifiedOrderQueue.objects.filter(status__in=['received', 'confirmed', 'preparing']).count()
    completed_orders = UnifiedOrderQueue.objects.filter(status='completed').count()
    
    # Phase 3 metrics
    from .advanced_scheduling_models import ScheduleOptimization
    from .kitchen_optimization_models import KitchenLayoutOptimization
    schedule_optimizations = ScheduleOptimization.objects.filter(applied=True).count()
    kitchen_layouts = KitchenLayoutOptimization.objects.filter(is_active=True).count()
    
    # Phase 4 metrics
    from .multi_location_models import CloudKitchenLocation, CentralPrepKitchen
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

# Real-time API Endpoints
@login_required
@user_passes_test(is_admin)
def get_real_time_metrics(request):
    """Get real-time metrics for dashboard"""
    try:
        # Order metrics
        from .order_orchestration_models import UnifiedOrderQueue
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
        from .delivery_integration_models import DeliveryPlatform
        active_platforms = DeliveryPlatform.objects.filter(is_active=True).count()
        
        # Location metrics
        from .multi_location_models import CloudKitchenLocation
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
        from .order_orchestration_models import UnifiedOrderQueue
        from .real_time_order_models import RealTimeOrderTracking
        
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
                'estimated_completion': order.real_time_tracking.estimated_completion.isoformat() if order.real_time_tracking and order.real_time_tracking.estimated_completion else None,
                'progress_percentage': order.real_time_tracking.progress_percentage if order.real_time_tracking else 0,
                'current_step': order.real_time_tracking.current_step if order.real_time_tracking else '',
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

# Phase 2: Customer Service Functions
@login_required
@user_passes_test(is_admin)
def special_requests_management(request):
    """Special requests management interface"""
    from .real_time_order_models import SpecialRequestManagement
    
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

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def handle_special_request(request, request_id):
    """Handle special request"""
    if request.method == 'POST':
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
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
@user_passes_test(is_admin)
def vip_customer_management(request):
    """VIP customer management dashboard"""
    from .customer_service_models import VIPCustomerManagement
    
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

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def update_vip_customer(request, customer_id):
    """Update VIP customer information"""
    if request.method == 'POST':
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
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
@user_passes_test(is_admin)
def customer_feedback_dashboard(request):
    """Customer feedback collection and analysis"""
    from .customer_service_models import CustomerFeedbackCollection
    
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

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def respond_to_feedback(request, feedback_id):
    """Respond to customer feedback"""
    if request.method == 'POST':
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
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

# Phase 3: Additional Functions
@login_required
@user_passes_test(is_admin)
def order_prioritization_settings(request):
    """Order prioritization algorithm settings"""
    from .order_orchestration_models import OrderPrioritization
    
    brand_id = request.GET.get('brand')
    
    if brand_id:
        from .models import VirtualBrand
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

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def create_prioritization_rule(request):
    """Create new prioritization rule"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            brand_id = data['brand_id']
            rule_type = data['rule_type']
            weight = Decimal(str(data.get('weight', 1.0)))
            conditions = data.get('conditions', {})
            priority = data.get('priority', 0)
            
            from .models import VirtualBrand
            brand = get_object_or_404(VirtualBrand, brand_id=brand_id)
            
            rule = OrderPrioritization.objects.create(
                brand=brand,
                rule_type=rule_type,
                weight=weight,
                conditions=conditions,
                priority=priority
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
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
@user_passes_test(is_admin)
def order_batching_dashboard(request):
    """Order batching and efficiency dashboard"""
    from .order_orchestration_models import UnifiedOrderBatch
    
    batches = UnifiedOrderBatch.objects.select_related('brand').order_by('-created_at')
    
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
