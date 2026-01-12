import json
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Avg, Count, Q
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from .models import VirtualBrand, PlatformIntegration, BrandPerformance, MenuOptimization, SharedIngredient, GhostKitchenWorkflow
from .models import Menu, RecipeMenuItem, Ingredient, RecipeIngredient

def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def platform_integration(request):
    """Platform integration management"""
    brands = VirtualBrand.objects.all()
    integrations = PlatformIntegration.objects.select_related('brand').all()
    
    # Get platform statistics
    platform_stats = {
        'uber_eats': integrations.filter(platform='uber_eats', is_active=True).count(),
        'doordash': integrations.filter(platform='doordash', is_active=True).count(),
        'grubhub': integrations.filter(platform='grubhub', is_active=True).count(),
    }
    
    context = {
        'brands': brands,
        'integrations': integrations,
        'platform_stats': platform_stats,
    }
    return render(request, 'menu_management/platform_integration.html', context)

@login_required
@user_passes_test(is_admin)
def sync_platform_menu(request, brand_id, platform):
    """Sync menu with delivery platform"""
    brand = get_object_or_404(VirtualBrand, id=brand_id)
    
    if request.method == 'POST':
        try:
            # Get brand menus
            menus = Menu.objects.filter(brand=brand)
            menu_data = []
            
            for menu in menus:
                sections = menu.sections.all()
                menu_sections = []
                
                for section in sections:
                    items = section.items.filter(is_available=True)
                    section_items = []
                    
                    for item in items:
                        section_items.append({
                            'name': item.name,
                            'description': item.description,
                            'price': float(item.price),
                            'available': item.is_available,
                            'prep_time': item.prep_time or 15,
                            'dietary_info': item.dietary_info or {},
                        })
                    
                    menu_sections.append({
                        'name': section.name,
                        'description': section.description,
                        'items': section_items
                    })
                
                menu_data.append({
                    'name': menu.name,
                    'description': menu.description,
                    'menu_type': menu.menu_type,
                    'sections': menu_sections
                })
            
            # Mock API call to platform
            success = mock_platform_sync(platform, menu_data, brand)
            
            if success:
                # Update integration status
                integration, created = PlatformIntegration.objects.get_or_create(
                    brand=brand,
                    platform=platform,
                    defaults={'sync_status': 'success', 'last_sync': timezone.now()}
                )
                
                if not created:
                    integration.sync_status = 'success'
                    integration.last_sync = timezone.now()
                    integration.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Menu synced successfully with {platform.replace("_", " ").title()}',
                    'sync_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Failed to sync menu with platform'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error syncing menu: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def mock_platform_sync(platform, menu_data, brand):
    """Mock platform sync - in real implementation, this would call actual platform APIs"""
    # Simulate API call delay
    import time
    time.sleep(1)
    
    # Mock success rate (90% success)
    import random
    return random.random() > 0.1

@login_required
@user_passes_test(is_admin)
def performance_analytics(request):
    """Performance analytics for virtual brands"""
    brands = VirtualBrand.objects.all()
    
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Default to last 30 days
    if not start_date:
        start_date = (timezone.now() - timezone.timedelta(days=30)).date()
    if not end_date:
        end_date = timezone.now().date()
    
    # Get performance data for each brand
    brand_performance = []
    for brand in brands:
        # Get or create performance data
        performance_data = BrandPerformance.objects.filter(
            brand=brand,
            date__gte=start_date,
            date__lte=end_date
        ).aggregate(
            total_orders=Sum('total_orders'),
            total_revenue=Sum('total_revenue'),
            avg_order_value=Avg('avg_order_value'),
            avg_rating=Avg('customer_ratings')
        )
        
        brand_performance.append({
            'brand': brand,
            'total_orders': performance_data['total_orders'] or 0,
            'total_revenue': performance_data['total_revenue'] or 0,
            'avg_order_value': performance_data['avg_order_value'] or 0,
            'avg_rating': performance_data['avg_rating'] or 0,
        })
    
    # Get top performing items across all brands
    top_items = []
    for brand in brands:
        brand_items = RecipeMenuItem.objects.filter(
            menu_section__menu__brand=brand,
            is_available=True
        ).annotate(
            order_count=Count('orderitem'),
            total_revenue=Sum('orderitem__total_price')
        ).order_by('-order_count')[:5]
        
        top_items.extend([
            {
                'brand': brand.name,
                'item_name': item.name,
                'order_count': item.order_count or 0,
                'revenue': item.total_revenue or 0,
            }
            for item in brand_items
        ])
    
    # Sort top items by revenue
    top_items.sort(key=lambda x: x['revenue'], reverse=True)
    top_items = top_items[:10]
    
    context = {
        'brand_performance': brand_performance,
        'top_items': top_items,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'menu_management/performance_analytics.html', context)

@login_required
@user_passes_test(is_admin)
def menu_optimization(request):
    """AI-powered menu optimization recommendations"""
    brands = VirtualBrand.objects.all()
    
    # Get optimization recommendations for each brand
    brand_recommendations = []
    for brand in brands:
        recommendations = MenuOptimization.objects.filter(brand=brand).order_by('-priority')
        
        # Generate mock recommendations if none exist
        if not recommendations.exists():
            recommendations = generate_mock_recommendations(brand)
        
        brand_recommendations.append({
            'brand': brand,
            'recommendations': recommendations,
        })
    
    context = {
        'brand_recommendations': brand_recommendations,
    }
    return render(request, 'menu_management/menu_optimization.html', context)

def generate_mock_recommendations(brand):
    """Generate mock AI recommendations for a brand"""
    recommendations = []
    
    # Pricing recommendations
    recommendations.append(MenuOptimization.objects.create(
        brand=brand,
        recommendation_type='pricing',
        priority='high',
        title='Increase prices on top 3 items by 10%',
        description='Based on demand elasticity, increasing prices on your most popular items could increase revenue by 15% without significantly impacting order volume.',
        expected_impact='Revenue increase of $2,500/month',
        implementation_status='pending'
    ))
    
    # Inventory recommendations
    recommendations.append(MenuOptimization.objects.create(
        brand=brand,
        recommendation_type='inventory',
        priority='medium',
        title='Optimize ingredient ordering for shared items',
        description='Consolidate ordering of shared ingredients across brands to reduce costs by 8%.',
        expected_impact='Cost reduction of $800/month',
        implementation_status='pending'
    ))
    
    # Menu mix recommendations
    recommendations.append(MenuOptimization.objects.create(
        brand=brand,
        recommendation_type='menu_mix',
        priority='medium',
        title='Add 2 new high-margin items',
        description='Introduce 2 new items with 70%+ margin based on current ingredient inventory and customer preferences.',
        expected_impact='Margin increase of 5%',
        implementation_status='pending'
    ))
    
    return recommendations

@login_required
@user_passes_test(is_admin)
def ghost_kitchen_operations(request):
    """Ghost kitchen workflow optimization"""
    brands = VirtualBrand.objects.all()
    
    # Get workflow data for each brand
    brand_workflows = []
    for brand in brands:
        workflows = GhostKitchenWorkflow.objects.filter(brand=brand)
        
        # Generate mock workflow data if none exists
        if not workflows.exists():
            workflows = generate_mock_workflows(brand)
        
        brand_workflows.append({
            'brand': brand,
            'workflows': workflows,
        })
    
    # Get shared ingredients data
    shared_ingredients = SharedIngredient.objects.select_related('ingredient', 'brand').all()
    
    context = {
        'brand_workflows': brand_workflows,
        'shared_ingredients': shared_ingredients,
    }
    return render(request, 'menu_management/ghost_kitchen_operations.html', context)

def generate_mock_workflows(brand):
    """Generate mock workflow data for a brand"""
    workflows = []
    
    stations = ['Prep Station', 'Cooking Station', 'Packaging Station', 'Quality Control']
    
    for station in stations:
        workflow = GhostKitchenWorkflow.objects.create(
            brand=brand,
            station_name=station,
            avg_preparation_time=15,  # Mock time in minutes
            capacity_per_hour=40,  # Mock capacity
            efficiency_score=85.5,  # Mock efficiency
            optimization_suggestions=[
                'Reduce prep time by 20%',
                'Increase capacity by 15%',
                'Optimize station layout'
            ]
        )
        workflows.append(workflow)
    
    return workflows

@login_required
@user_passes_test(is_admin)
def unified_management(request):
    """Unified management dashboard for all brands"""
    brands = VirtualBrand.objects.all()
    
    # Get unified statistics
    total_brands = brands.count()
    active_brands = brands.filter(is_active=True).count()
    
    # Get shared ingredients across all brands
    shared_ingredients_count = SharedIngredient.objects.values('ingredient').distinct().count()
    
    # Get total menu items across all brands
    total_menu_items = RecipeMenuItem.objects.filter(
        menu_section__menu__brand__in=brands
    ).count()
    
    # Get platform integrations
    platform_integrations = PlatformIntegration.objects.filter(is_active=True).count()
    
    context = {
        'brands': brands,
        'total_brands': total_brands,
        'active_brands': active_brands,
        'shared_ingredients_count': shared_ingredients_count,
        'total_menu_items': total_menu_items,
        'platform_integrations': platform_integrations,
    }
    return render(request, 'menu_management/unified_management.html', context)

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def create_virtual_brand(request):
    """Create new virtual brand"""
    if request.method == 'POST':
        try:
            brand = VirtualBrand.objects.create(
                name=request.POST.get('name'),
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
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})
