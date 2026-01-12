from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.db.models import Q
import json
import re
from difflib import SequenceMatcher

# Global search registry - includes all apps and modules
GLOBAL_SEARCH_REGISTRY = {
    # Menu Management
    'menu_dashboard': {
        'title': 'Menu Management Dashboard',
        'url': '/menu-management/',
        'description': 'Main menu management dashboard',
        'keywords': ['menu', 'dashboard', 'main', 'home'],
        'category': 'Menu Management',
        'app': 'menu_management'
    },
    'recipes': {
        'title': 'Recipes',
        'url': '/menu-management/recipes/',
        'description': 'Manage recipes and cooking instructions',
        'keywords': ['recipe', 'recipes', 'cooking', 'ingredients'],
        'category': 'Menu Management',
        'app': 'menu_management'
    },
    'menu_items': {
        'title': 'Menu Items',
        'url': '/menu-management/menu-items/',
        'description': 'Manage menu items and pricing',
        'keywords': ['menu item', 'item', 'food', 'dish', 'price'],
        'category': 'Menu Management',
        'app': 'menu_management'
    },
    'course_templates': {
        'title': 'Course Menu Templates',
        'url': '/menu-management/courses/templates/',
        'description': 'Manage course menu templates',
        'keywords': ['course', 'template', 'menu template', 'tasting menu'],
        'category': 'Menu Management',
        'app': 'menu_management'
    },
    'tasks': {
        'title': 'Task Management',
        'url': '/menu-management/tasks/',
        'description': 'Manage kitchen tasks and assignments',
        'keywords': ['task', 'tasks', 'assignment', 'kitchen', 'staff'],
        'category': 'Operations',
        'app': 'menu_management'
    },
    'inventory': {
        'title': 'Inventory Management',
        'url': '/menu-management/inventory/',
        'description': 'Manage inventory and stock levels',
        'keywords': ['inventory', 'stock', 'items', 'products', 'materials'],
        'category': 'Operations',
        'app': 'menu_management'
    },
    'stations': {
        'title': 'Station Management',
        'url': '/menu-management/stations/',
        'description': 'Manage kitchen stations and workflow',
        'keywords': ['station', 'kitchen', 'workflow', 'prep'],
        'category': 'Operations',
        'app': 'menu_management'
    },
    'kitchen_display': {
        'title': 'Kitchen Display System',
        'url': '/menu-management/kitchen/',
        'description': 'Kitchen order display and management',
        'keywords': ['kitchen', 'display', 'orders', 'kds'],
        'category': 'Operations',
        'app': 'menu_management'
    },
    'analytics': {
        'title': 'Analytics Dashboard',
        'url': '/menu-management/analytics/',
        'description': 'View analytics and reports',
        'keywords': ['analytics', 'reports', 'statistics', 'data'],
        'category': 'Analytics',
        'app': 'menu_management'
    },
    
    # Orders App
    'orders_dashboard': {
        'title': 'Orders Dashboard',
        'url': '/orders/dashboard/',
        'description': 'Main orders management dashboard',
        'keywords': ['orders', 'dashboard', 'order management'],
        'category': 'Orders',
        'app': 'orders'
    },
    'cart': {
        'title': 'Shopping Cart',
        'url': '/cart/',
        'description': 'View and manage shopping cart',
        'keywords': ['cart', 'shopping', 'basket', 'items'],
        'category': 'Orders',
        'app': 'orders'
    },
    'checkout': {
        'title': 'Checkout',
        'url': '/checkout/',
        'description': 'Complete your order checkout',
        'keywords': ['checkout', 'payment', 'buy', 'purchase'],
        'category': 'Orders',
        'app': 'orders'
    },
    'order_status': {
        'title': 'Order Status',
        'url': '/order-status/',
        'description': 'Check your order status',
        'keywords': ['order status', 'tracking', 'delivery'],
        'category': 'Orders',
        'app': 'orders'
    },
    'kitchen_orders': {
        'title': 'Kitchen Orders',
        'url': '/orders/kitchen/',
        'description': 'Kitchen order management',
        'keywords': ['kitchen orders', 'cooking', 'prep'],
        'category': 'Orders',
        'app': 'orders'
    },
    'meal_pass': {
        'title': 'Meal Pass Options',
        'url': '/meal-pass/',
        'description': 'View and purchase meal passes',
        'keywords': ['meal pass', 'subscription', 'meal plan'],
        'category': 'Orders',
        'app': 'orders'
    },
    'user_management': {
        'title': 'User Management',
        'url': '/account/users/',
        'description': 'Manage users and accounts',
        'keywords': ['users', 'accounts', 'admin', 'staff'],
        'category': 'Admin',
        'app': 'orders'
    },
    'admin_profile': {
        'title': 'Admin Profile',
        'url': '/admin/profile/',
        'description': 'Admin profile and settings',
        'keywords': ['admin', 'profile', 'settings', 'account'],
        'category': 'Admin',
        'app': 'orders'
    },
    
    # Customer App
    'customer_signup': {
        'title': 'Customer Signup',
        'url': '/customer/signup/',
        'description': 'Create a new customer account',
        'keywords': ['signup', 'register', 'new account', 'customer'],
        'category': 'Customer',
        'app': 'customer'
    },
    'customer_login': {
        'title': 'Customer Login',
        'url': '/customer/login/',
        'description': 'Login to your customer account',
        'keywords': ['login', 'signin', 'customer login'],
        'category': 'Customer',
        'app': 'customer'
    },
    
    # Django Admin
    'django_admin': {
        'title': 'Django Admin',
        'url': '/admin/',
        'description': 'Django administration panel',
        'keywords': ['admin', 'django admin', 'administration'],
        'category': 'Admin',
        'app': 'django'
    }
}

def calculate_similarity(query, item_data):
    """Calculate similarity score between query and item data"""
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    score = 0.0
    
    # Title similarity (highest weight)
    title_words = set(item_data['title'].lower().split())
    title_similarity = len(query_words & title_words) / len(query_words | title_words) if query_words | title_words else 0
    score += title_similarity * 0.4
    
    # Keywords matching (high weight)
    for keyword in item_data['keywords']:
        keyword_lower = keyword.lower()
        if keyword_lower == query_lower:
            score += 0.5
        elif keyword_lower in query_lower:
            score += 0.3
        elif any(word in keyword_lower for word in query_lower.split()):
            score += 0.2
    
    # Description similarity (medium weight)
    desc_words = set(item_data['description'].lower().split())
    desc_similarity = len(query_words & desc_words) / len(query_words | desc_words) if query_words | desc_words else 0
    score += desc_similarity * 0.2
    
    # Category matching (low weight)
    category_lower = item_data['category'].lower()
    if category_lower in query_lower:
        score += 0.1
    
    return min(score, 1.0)  # Cap at 1.0

@require_GET
def global_search(request):
    """Global search endpoint - works across all apps"""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({
            'results': [],
            'suggestions': [],
            'query': query
        })
    
    # Calculate similarity scores for all items
    results = []
    for key, item_data in GLOBAL_SEARCH_REGISTRY.items():
        similarity_score = calculate_similarity(query, item_data)
        
        if similarity_score > 0.2:  # Threshold for relevance
            result = {
                'key': key,
                'title': item_data['title'],
                'url': item_data['url'],
                'description': item_data['description'],
                'category': item_data['category'],
                'app': item_data['app'],
                'similarity': similarity_score
            }
            results.append(result)
    
    # Sort by similarity score
    results.sort(key=lambda x: x['similarity'], reverse=True)
    
    # Generate suggestions based on partial matches
    suggestions = []
    for key, item_data in GLOBAL_SEARCH_REGISTRY.items():
        if query_lower := query.lower():
            if (query_lower in item_data['title'].lower() or 
                any(query_lower in kw.lower() for kw in item_data['keywords'])):
                suggestions.append({
                    'text': item_data['title'],
                    'description': item_data['description'],
                    'url': item_data['url']
                })
    
    # Limit suggestions
    suggestions = suggestions[:5]
    
    return JsonResponse({
        'results': results[:10],  # Top 10 results
        'suggestions': suggestions,
        'query': query
    })

@require_GET
def global_search_suggestions(request):
    """Global search suggestions endpoint"""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    suggestions = []
    query_lower = query.lower()
    
    for key, item_data in GLOBAL_SEARCH_REGISTRY.items():
        # Check if query matches title or keywords
        if (query_lower in item_data['title'].lower() or 
            any(query_lower in kw.lower() for kw in item_data['keywords'])):
            suggestions.append({
                'text': item_data['title'],
                'description': item_data['description'],
                'url': item_data['url'],
                'category': item_data['category']
            })
    
    # Sort by relevance (exact matches first)
    suggestions.sort(key=lambda x: (
        query_lower == x['text'].lower(),  # Exact match first
        query_lower in x['text'].lower(),  # Then partial matches
    ), reverse=True)
    
    return JsonResponse({'suggestions': suggestions[:5]})

def global_search_page(request):
    """Full search page with results"""
    query = request.GET.get('query', '').strip()
    results = []
    
    if query and len(query) >= 2:
        for key, item_data in GLOBAL_SEARCH_REGISTRY.items():
            similarity_score = calculate_similarity(query, item_data)
            
            if similarity_score > 0.2:
                result = {
                    'key': key,
                    'title': item_data['title'],
                    'url': item_data['url'],
                    'description': item_data['description'],
                    'category': item_data['category'],
                    'app': item_data['app'],
                    'similarity': similarity_score
                }
                results.append(result)
        
        results.sort(key=lambda x: x['similarity'], reverse=True)
    
    return render(request, 'global_search.html', {
        'query': query,
        'results': results,
        'categories': sorted(set(item['category'] for item in GLOBAL_SEARCH_REGISTRY.values()))
    })
