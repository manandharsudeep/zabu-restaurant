from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import Menu, RecipeMenuItem
import json

@csrf_exempt
@require_http_methods(["GET", "POST"])
def digital_menu_board_api(request, brand_id=None):
    """API for external digital menu board displays"""
    
    # Get menu items for the specified brand or all menus
    if brand_id:
        try:
            menu = Menu.objects.get(id=brand_id, is_active=True)
            menu_items = RecipeMenuItem.objects.filter(menu_section__menu=menu, is_available=True)
        except Menu.DoesNotExist:
            return JsonResponse({'error': 'Menu not found'}, status=404)
    else:
        # Get all active menu items
        menu_items = RecipeMenuItem.objects.filter(is_available=True)
    
    # Format for digital menu boards
    menu_data = {
        'timestamp': timezone.now().isoformat(),
        'brand_id': brand_id,
        'menu_items': []
    }
    
    for item in menu_items:
        menu_item_data = {
            'id': item.id,
            'name': item.name,
            'description': item.description,
            'price': str(item.price),
            'category': item.menu_section.name if item.menu_section else 'Uncategorized',
            'allergens': getattr(item, 'allergen_info', ''),
            'available': item.is_available,
            'image_url': getattr(item, 'image', {}).url if hasattr(item, 'image') and item.image else '',
            'preparation_time': item.prep_time or 0,
            'spicy_level': getattr(item, 'spicy_level', 0),
            'dietary': getattr(item, 'dietary_info', ''),
        }
        menu_data['menu_items'].append(menu_item_data)
    
    return JsonResponse(menu_data)

@csrf_exempt
@require_http_methods(["GET"])
def digital_menu_board_categories(request):
    """Get menu categories for digital menu board"""
    categories = RecipeMenuItem.objects.values_list('menu_section__name', flat=True).distinct()
    
    return JsonResponse({
        'categories': list(categories)
    })

@csrf_exempt
@require_http_methods(["GET"])
def digital_menu_board_item_detail(request, item_id):
    """Get detailed information for a specific menu item"""
    try:
        item = RecipeMenuItem.objects.get(id=item_id, is_available=True)
        
        item_data = {
            'id': item.id,
            'name': item.name,
            'description': item.description,
            'price': str(item.price),
            'category': item.menu_section.name if item.menu_section else 'Uncategorized',
            'allergens': getattr(item, 'allergen_info', ''),
            'available': item.is_available,
            'image_url': getattr(item, 'image', {}).url if hasattr(item, 'image') and item.image else '',
            'preparation_time': item.prep_time or 0,
            'spicy_level': getattr(item, 'spicy_level', 0),
            'dietary': getattr(item, 'dietary_info', ''),
            'ingredients': [],
            'nutrition': getattr(item, 'nutrition_info', {}),
        }
        
        # Add ingredients if available
        if hasattr(item, 'recipe') and hasattr(item.recipe, 'ingredients'):
            item_data['ingredients'] = [
                {
                    'name': ing.ingredient.name,
                    'quantity': ing.quantity,
                    'unit': ing.unit
                }
                for ing in item.recipe.ingredients.all()
            ]
        
        return JsonResponse(item_data)
        
    except RecipeMenuItem.DoesNotExist:
        return JsonResponse({'error': 'Menu item not found'}, status=404)

@csrf_exempt
@require_http_methods(["POST"])
def update_menu_availability(request):
    """Update menu item availability for digital boards"""
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        available = data.get('available')
        
        item = RecipeMenuItem.objects.get(id=item_id)
        item.is_available = available
        item.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Item {item.name} availability updated to {available}'
        })
        
    except RecipeMenuItem.DoesNotExist:
        return JsonResponse({'error': 'Menu item not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)

@csrf_exempt
@require_http_methods(["GET"])
def digital_menu_board_status(request):
    """Get system status for digital menu boards"""
    total_menus = Menu.objects.filter(is_active=True).count()
    total_items = RecipeMenuItem.objects.filter(is_available=True).count()
    available_items = RecipeMenuItem.objects.filter(is_available=True).count()
    
    return JsonResponse({
        'status': 'operational',
        'timestamp': timezone.now().isoformat(),
        'total_menus': total_menus,
        'total_items': total_items,
        'available_items': available_items,
        'last_updated': timezone.now().isoformat(),
    })

@csrf_exempt
@require_http_methods(["GET"])
def digital_menu_board_sync(request):
    """Trigger menu synchronization for digital boards"""
    # This would typically trigger a webhook or push notification
    # For now, return success
    return JsonResponse({
        'success': True,
        'message': 'Menu synchronization triggered',
        'timestamp': timezone.now().isoformat()
    })
