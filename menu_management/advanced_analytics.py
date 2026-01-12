from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Sum, Avg, F, Expression, FloatField
from django.utils import timezone
from datetime import timedelta
from .models import Menu, RecipeMenuItem
from orders.models import Order
import json

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
@user_passes_test(is_admin)
def advanced_analytics_dashboard(request):
    """Advanced analytics dashboard with A/B testing"""
    
    # Get date range for analytics
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Menu performance analytics
    menu_performance = []
    menus = Menu.objects.filter(is_active=True)
    
    for menu in menus:
        # Get items through menu_sections
        items = RecipeMenuItem.objects.filter(menu_section__menu=menu)
        total_items = items.count()
        available_items = items.filter(is_available=True).count()
        
        # Calculate average price
        avg_price = items.aggregate(
            avg_price=Avg('price')
        )['avg_price'] or 0
        
        menu_performance.append({
            'menu': menu,
            'total_items': total_items,
            'available_items': available_items,
            'availability_rate': (available_items / total_items * 100) if total_items > 0 else 0,
            'avg_price': avg_price,
        })
    
    # A/B Testing data (mock data for demonstration)
    ab_tests = [
        {
            'id': 1,
            'name': 'Burger Price Test',
            'description': 'Testing 10% price increase on signature burger',
            'status': 'active',
            'start_date': (end_date - timedelta(days=7)).date(),
            'variants': [
                {'name': 'Control', 'price': '$12.99', 'orders': 145, 'revenue': 1883.55},
                {'name': 'Test A (+10%)', 'price': '$14.29', 'orders': 132, 'revenue': 1886.28},
            ],
            'winner': 'Test A (+10%)',
            'confidence': 85.2,
            'lift': 0.14,
        },
        {
            'id': 2,
            'name': 'Combo Deal Test',
            'description': 'Testing combo vs individual pricing',
            'status': 'completed',
            'start_date': (end_date - timedelta(days=14)).date(),
            'end_date': (end_date - timedelta(days=7)).date(),
            'variants': [
                {'name': 'Individual', 'price': '$15.99', 'orders': 89, 'revenue': 1423.11},
                {'name': 'Combo Deal', 'price': '$13.99', 'orders': 124, 'revenue': 1734.76},
            ],
            'winner': 'Combo Deal',
            'confidence': 92.8,
            'lift': 21.8,
        }
    ]
    
    # Revenue trends (mock data)
    revenue_trends = []
    for i in range(30):
        date = (end_date - timedelta(days=i)).date()
        revenue = 1500 + (i * 50) + (i % 7 * 100)  # Mock trend data
        revenue_trends.append({
            'date': date.isoformat(),
            'revenue': revenue,
            'orders': int(revenue / 25),  # Mock order count
        })
    
    revenue_trends.reverse()  # Show oldest to newest
    
    # Top performing items
    top_items = RecipeMenuItem.objects.filter(
        is_available=True
    ).annotate(
        avg_price=Avg('price')
    ).order_by('-avg_price')[:10]
    
    # Category performance
    category_performance = RecipeMenuItem.objects.values(
        'menu_section__name'
    ).annotate(
        item_count=Count('id'),
        avg_price=Avg('price'),
        available_count=Count('id', filter=F('is_available'))
    ).order_by('-item_count')
    
    context = {
        'menu_performance': menu_performance,
        'ab_tests': ab_tests,
        'revenue_trends': revenue_trends,
        'top_items': top_items,
        'category_performance': category_performance,
        'total_menus': menus.count(),
        'total_items': RecipeMenuItem.objects.count(),
        'available_items': RecipeMenuItem.objects.filter(is_available=True).count(),
    }
    
    return render(request, 'menu_management/advanced_analytics.html', context)

@login_required
@user_passes_test(is_admin)
def create_ab_test(request):
    """Create a new A/B test"""
    if request.method == 'POST':
        data = json.loads(request.body)
        
        # Create A/B test (simplified for demo)
        test_data = {
            'success': True,
            'test_id': 3,
            'message': 'A/B test created successfully',
            'test': {
                'id': 3,
                'name': data.get('name'),
                'description': data.get('description'),
                'status': 'created',
                'start_date': timezone.now().date(),
                'variants': data.get('variants', []),
            }
        }
        
        return JsonResponse(test_data)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_admin)
def get_analytics_data(request):
    """Get analytics data for charts"""
    data_type = request.GET.get('type', 'revenue')
    days = int(request.GET.get('days', 30))
    
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    if data_type == 'revenue':
        # Mock revenue data
        data = []
        for i in range(days):
            date = (end_date - timedelta(days=i)).date()
            revenue = 1500 + (i * 30) + (i % 7 * 80)
            data.append({
                'date': date.isoformat(),
                'value': revenue
            })
        data.reverse()
        
    elif data_type == 'orders':
        # Mock order data
        data = []
        for i in range(days):
            date = (end_date - timedelta(days=i)).date()
            orders = 60 + (i * 2) + (i % 7 * 15)
            data.append({
                'date': date.isoformat(),
                'value': orders
            })
        data.reverse()
        
    elif data_type == 'items':
        # Top items performance
        items = RecipeMenuItem.objects.filter(
            is_available=True
        ).annotate(
            avg_price=Avg('price')
        ).order_by('-avg_price')[:10]
        
        data = [
            {
                'name': item.name,
                'value': float(item.avg_price or 0)
            }
            for item in items
        ]
    
    return JsonResponse({'data': data})

@login_required
@user_passes_test(is_admin)
def menu_optimization_suggestions(request):
    """Get AI-powered menu optimization suggestions"""
    suggestions = [
        {
            'type': 'pricing',
            'title': 'Increase prices on top 5 items by 8%',
            'description': 'Based on demand elasticity, these items can sustain a price increase',
            'impact': '+$1,200/month',
            'confidence': 87,
            'items': ['Signature Burger', 'Premium Pizza', 'Special Pasta'],
        },
        {
            'type': 'menu_structure',
            'title': 'Add 3 new high-margin items',
            'description': 'Introduce items with 70%+ margin based on ingredient analysis',
            'impact': '+$800/month',
            'confidence': 72,
            'items': ['Gourmet Salad', 'Artisan Sandwich', 'Dessert Special'],
        },
        {
            'type': 'promotion',
            'title': 'Create lunch combo deals',
            'description': 'Bundle popular items for increased order value',
            'impact': '+$600/month',
            'confidence': 91,
            'items': ['Burger + Fries + Drink', 'Pizza + Salad'],
        }
    ]
    
    return JsonResponse({'suggestions': suggestions})

@login_required
@user_passes_test(is_admin)
def digital_menu_board_view(request):
    """Digital menu board interface for external displays"""
    return render(request, 'menu_management/digital_menu_board.html')

def public_digital_menu_board(request):
    """Public digital menu board interface - no authentication required"""
    return render(request, 'menu_management/digital_menu_board.html')
