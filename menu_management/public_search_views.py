from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET
import json
import re
from difflib import SequenceMatcher

# Global function registry with natural language patterns
FUNCTION_REGISTRY = {
    # Inventory Management
    'purchase_orders': {
        'title': 'Purchase Orders',
        'url': '/menu-management/inventory/purchase-orders/',
        'description': 'Manage and track purchase orders with vendors',
        'keywords': ['purchase order', 'vendor', 'buy', 'procurement', 'new vendor', 'add vendor', 'create purchase', 'input purchases', 'inventory purchase', 'vendor list'],
        'category': 'Inventory'
    },
    'create_purchase_order': {
        'title': 'Create Purchase Order',
        'url': '/menu-management/inventory/purchase-orders/create/',
        'description': 'Create a new purchase order for inventory',
        'keywords': ['new purchase order', 'create purchase', 'add purchase', 'new vendor', 'vendor order', 'buy inventory', 'vendor list'],
        'category': 'Inventory'
    },
    'create_vendor': {
        'title': 'Create Vendor',
        'url': '/menu-management/inventory/items/create/',
        'description': 'Add a new vendor to your supplier database',
        'keywords': ['new vendor', 'create vendor', 'add vendor', 'vendor management', 'supplier', 'new supplier', 'add supplier', 'vendor list', 'existing vendor', 'vendor database'],
        'category': 'Inventory'
    },
    'inventory_items': {
        'title': 'Inventory Items',
        'url': '/menu-management/inventory/items/',
        'description': 'Manage inventory items and stock levels',
        'keywords': ['inventory', 'items', 'stock', 'products', 'goods', 'materials', 'reorder', 'reorder ingredients', 'new inventory item', 'create inventory item'],
        'category': 'Inventory'
    },
    'create_inventory_item': {
        'title': 'Create Inventory Item',
        'url': '/menu-management/inventory/items/create/',
        'description': 'Add new inventory item for reordering ingredients',
        'keywords': ['new inventory item', 'create inventory item', 'add inventory item', 'reorder ingredients', 'stock ingredients', 'inventory reorder', 'new stock item'],
        'category': 'Inventory'
    },
    'inventory_transactions': {
        'title': 'Inventory Transactions',
        'url': '/menu-management/inventory/transactions/',
        'description': 'View inventory movement history',
        'keywords': ['transactions', 'movement', 'history', 'log', 'record'],
        'category': 'Inventory'
    },
    'waste_tracking': {
        'title': 'Waste Tracking',
        'url': '/menu-management/inventory/waste/',
        'description': 'Track and manage waste and spoilage',
        'keywords': ['waste', 'spoilage', 'loss', 'disposal', 'expired'],
        'category': 'Inventory'
    },
    'inventory_reports': {
        'title': 'Inventory Reports',
        'url': '/menu-management/inventory/reports/',
        'description': 'Generate inventory reports and analytics',
        'keywords': ['reports', 'analytics', 'inventory reports', 'cost analysis'],
        'category': 'Inventory'
    },
    
    # Menu Management
    'menus': {
        'title': 'Menu Management',
        'url': '/menu-management/menus/',
        'description': 'Manage restaurant menus and pricing',
        'keywords': ['menu', 'food menu', 'dishes', 'offerings', 'restaurant menu'],
        'category': 'Menu'
    },
    'create_menu': {
        'title': 'Create Menu',
        'url': '/menu-management/menus/create/',
        'description': 'Create a new menu',
        'keywords': ['new menu', 'create menu', 'add menu', 'menu design'],
        'category': 'Menu'
    },
    'create_menu_item': {
        'title': 'Create Menu Item',
        'url': '/menu-management/menu-items/create/',
        'description': 'Add a new dish to your restaurant menu',
        'keywords': ['new menu item', 'create menu item', 'add menu item', 'new dish', 'create dish', 'add dish', 'order item', 'menu item'],
        'category': 'Menu'
    },
    'recipes': {
        'title': 'Recipes',
        'url': '/menu-management/recipes/',
        'description': 'Manage recipe database and instructions',
        'keywords': ['recipes', 'cooking', 'instructions', 'preparation', 'dish recipes'],
        'category': 'Menu'
    },
    'create_recipe': {
        'title': 'Create Recipe',
        'url': '/menu-management/recipes/create/',
        'description': 'Create a new recipe with ingredients',
        'keywords': ['new recipe', 'create recipe', 'add recipe', 'recipe creation'],
        'category': 'Menu'
    },
    
    # Kitchen Operations
    'kitchen_operations': {
        'title': 'Kitchen Operations',
        'url': '/menu-management/kitchen/',
        'description': 'Kitchen display and operations',
        'keywords': ['kitchen', 'cooking', 'operations', 'food prep', 'chef'],
        'category': 'Kitchen'
    },
    'station_management': {
        'title': 'Station Management',
        'url': '/menu-management/stations/',
        'description': 'Manage kitchen stations',
        'keywords': ['stations', 'kitchen stations', 'work stations', 'prep areas'],
        'category': 'Kitchen'
    },
    
    # Analytics & Reports
    'analytics_dashboard': {
        'title': 'Analytics Dashboard',
        'url': '/menu-management/analytics/',
        'description': 'Business analytics and insights',
        'keywords': ['analytics', 'insights', 'business intelligence', 'data', 'metrics'],
        'category': 'Analytics'
    },
    'performance_analytics': {
        'title': 'Performance Analytics',
        'url': '/menu-management/performance/',
        'description': 'Performance metrics and KPIs',
        'keywords': ['performance', 'kpi', 'metrics', 'efficiency', 'productivity'],
        'category': 'Analytics'
    },
    
    # Advanced Features
    'virtual_brands': {
        'title': 'Virtual Brands',
        'url': '/menu-management/virtual-brands/',
        'description': 'Manage virtual restaurant brands',
        'keywords': ['virtual brands', 'brands', 'multi-brand', 'restaurant brands'],
        'category': 'Advanced'
    },
    'platform_integrations': {
        'title': 'Platform Integrations',
        'url': '/menu-management/integrations/',
        'description': 'Manage delivery platform integrations',
        'keywords': ['integrations', 'delivery', 'platforms', 'uber eats', 'doordash'],
        'category': 'Advanced'
    },
    'unified_management': {
        'title': 'Unified Management',
        'url': '/menu-management/unified-management/',
        'description': 'Unified management dashboard',
        'keywords': ['unified', 'management', 'dashboard', 'overview', 'central'],
        'category': 'Advanced'
    }
}

def public_intelligent_search(request):
    """Public intelligent search with natural language processing"""
    if request.method == 'GET':
        return render(request, 'menu_management/public_intelligent_search.html')
    
    elif request.method == 'POST':
        query = request.POST.get('query', '').strip().lower()
        
        if not query:
            return JsonResponse({'results': [], 'suggestions': []})
        
        # Process natural language query
        results = []
        suggestions = []
        
        # Calculate similarity scores for all functions
        for func_key, func_data in FUNCTION_REGISTRY.items():
            similarity_score = calculate_similarity(query, func_data)
            
            if similarity_score > 0.2:  # Lower threshold for more inclusive results
                result = {
                    'key': func_key,
                    'title': func_data['title'],
                    'url': func_data['url'],
                    'description': func_data['description'],
                    'category': func_data['category'],
                    'similarity': similarity_score
                }
                results.append(result)
        
        # Sort by similarity score
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Generate suggestions based on partial matches
        suggestions = generate_suggestions(query)
        
        return JsonResponse({
            'results': results[:10],  # Top 10 results
            'suggestions': suggestions[:5],  # Top 5 suggestions
            'query': query
        })

def calculate_similarity(query, func_data):
    """Calculate similarity score between query and function data"""
    query_words = set(query.split())
    
    # Check title similarity
    title_words = set(func_data['title'].lower().split())
    title_similarity = len(query_words & title_words) / len(query_words | title_words)
    
    # Check keywords similarity
    keywords_text = ' '.join(func_data['keywords']).lower()
    keyword_similarity = 0
    for keyword in func_data['keywords']:
        if keyword in query:
            keyword_similarity += 0.5
        elif any(word in keyword for word in query.split()):
            keyword_similarity += 0.3
    
    # Check description similarity
    desc_words = set(func_data['description'].lower().split())
    desc_similarity = len(query_words & desc_words) / len(query_words | desc_words)
    
    # Fuzzy matching using SequenceMatcher
    fuzzy_score = 0
    for keyword in func_data['keywords']:
        fuzzy_score = max(fuzzy_score, SequenceMatcher(None, query, keyword).ratio())
    
    # Combined score with weights
    total_score = (
        title_similarity * 0.3 +
        keyword_similarity * 0.4 +
        desc_similarity * 0.1 +
        fuzzy_score * 0.2
    )
    
    return min(total_score, 1.0)

def generate_suggestions(query):
    """Generate autocomplete suggestions based on partial matches"""
    suggestions = []
    
    for func_key, func_data in FUNCTION_REGISTRY.items():
        # Check if query is partial match to any keyword
        for keyword in func_data['keywords']:
            if query in keyword and len(keyword) > len(query):
                suggestion = {
                    'text': keyword,
                    'description': func_data['title'],
                    'url': func_data['url']
                }
                if suggestion not in suggestions:
                    suggestions.append(suggestion)
                break
    
    return suggestions

@require_GET
def public_search_suggestions(request):
    """Provide autocomplete suggestions as user types"""
    query = request.GET.get('q', '').strip().lower()
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    suggestions = generate_suggestions(query)
    
    return JsonResponse({'suggestions': suggestions[:5]})
