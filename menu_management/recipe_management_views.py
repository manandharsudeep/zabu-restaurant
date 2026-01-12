from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.text import slugify
from django.core.paginator import Paginator
from django.urls import reverse
from decimal import Decimal
import json

from menu_management.models import Recipe, RecipeIngredient, RecipeMenuItemLink, Ingredient
from orders.models import MenuItem, Category, OrderItem
from django.contrib.auth.models import User

@login_required
def recipe_management_dashboard(request):
    """Comprehensive recipe management dashboard showing all recipes and their menu item connections"""
    
    # Get all recipes with enhanced information
    recipes = Recipe.objects.select_related('created_by').prefetch_related(
        'ingredients__ingredient',
        'menu_item_links__menu_item__category',
        'versions'
    ).annotate(
        menu_item_count=Count('menu_item_links'),
        ingredient_count=Count('ingredients'),
        total_cost=Sum('ingredients__ingredient__current_price')
    ).order_by('-created_at')
    
    # Get all menu items for linking
    menu_items = MenuItem.objects.select_related('category').prefetch_related('recipe_links__recipe')
    
    # Get statistics
    stats = {
        'total_recipes': Recipe.objects.count(),
        'active_recipes': Recipe.objects.filter(is_active=True).count(),
        'total_menu_items': MenuItem.objects.count(),
        'linked_items': RecipeMenuItemLink.objects.count(),
        'unlinked_menu_items': MenuItem.objects.filter(recipe_links__isnull=True).count(),
        'total_ingredients': Ingredient.objects.count(),
        'recipes_with_versions': Recipe.objects.filter(versions__isnull=False).distinct().count(),
    }
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        recipes = recipes.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(chef_notes__icontains=search_query)
        )
    
    # Filter by category (through menu items)
    category_filter = request.GET.get('category', '')
    if category_filter:
        recipes = recipes.filter(
            menu_item_links__menu_item__category_id=category_filter
        ).distinct()
    
    # Filter by availability
    availability_filter = request.GET.get('availability', '')
    if availability_filter == 'active':
        recipes = recipes.filter(is_active=True)
    elif availability_filter == 'inactive':
        recipes = recipes.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(recipes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for filter dropdown
    categories = Category.objects.all()
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'menu_items': menu_items,
        'categories': categories,
        'search_query': search_query,
        'category_filter': category_filter,
        'availability_filter': availability_filter,
    }
    
    return render(request, 'menu_management/recipe_management_dashboard.html', context)

@login_required
def recipe_detail(request, recipe_id):
    """Detailed view of a single recipe with all its connections"""
    
    recipe = get_object_or_404(Recipe, id=recipe_id)
    
    # Get recipe with all related data
    recipe = Recipe.objects.select_related('created_by').prefetch_related(
        'ingredients__ingredient',
        'menu_item_links__menu_item__category',
        'versions',
        'menu_item_links__menu_item__orderitem_set__order'
    ).get(id=recipe_id)
    
    # Calculate recipe cost
    total_cost = 0
    for recipe_ingredient in recipe.ingredients.all():
        ingredient_cost = recipe_ingredient.quantity * recipe_ingredient.ingredient.current_price
        total_cost += ingredient_cost
    
    # Get menu items using this recipe
    menu_items = recipe.menu_item_links.select_related('menu_item__category').all()
    
    # Get order history for menu items using this recipe
    order_items = OrderItem.objects.filter(
        menu_item__in=[link.menu_item for link in menu_items]
    ).select_related('order', 'menu_item').order_by('-order__created_at')[:10]
    
    # Get recipe versions
    versions = recipe.versions.order_by('-version_number')
    
    context = {
        'recipe': recipe,
        'total_cost': total_cost,
        'cost_per_portion': total_cost / recipe.portions if recipe.portions > 0 else 0,
        'menu_items': menu_items,
        'order_items': order_items,
        'versions': versions,
    }
    
    return render(request, 'menu_management/recipe_detail.html', context)

@login_required
@require_POST
def auto_link_recipes_to_menu_items(request):
    """Automatically link recipes to menu items based on name similarity"""
    
    linked_count = 0
    unlinked_menu_items = MenuItem.objects.filter(recipe_links__isnull=True)
    all_recipes = Recipe.objects.all()
    
    for menu_item in unlinked_menu_items:
        # Try to find matching recipe by name
        menu_item_name_lower = menu_item.name.lower().strip()
        
        for recipe in all_recipes:
            recipe_name_lower = recipe.name.lower().strip()
            
            # Check for exact match or very close match
            if (recipe_name_lower == menu_item_name_lower or 
                menu_item_name_lower in recipe_name_lower or 
                recipe_name_lower in menu_item_name_lower):
                
                # Create the link
                RecipeMenuItemLink.objects.get_or_create(
                    recipe=recipe,
                    menu_item=menu_item,
                    defaults={
                        'is_primary_recipe': True,
                        'auto_created': True,
                        'created_by': request.user
                    }
                )
                linked_count += 1
                break  # Stop after first match
    
    return JsonResponse({
        'success': True,
        'message': f'Successfully linked {linked_count} menu items to recipes',
        'linked_count': linked_count
    })

@login_required
@require_POST
def link_recipe_to_menu_item(request):
    """Manually link a recipe to a menu item"""
    
    recipe_id = request.POST.get('recipe_id')
    menu_item_id = request.POST.get('menu_item_id')
    is_primary = request.POST.get('is_primary', 'off') == 'on'
    
    recipe = get_object_or_404(Recipe, id=recipe_id)
    menu_item = get_object_or_404(MenuItem, id=menu_item_id)
    
    # If this is set as primary, unset other primary links
    if is_primary:
        RecipeMenuItemLink.objects.filter(
            menu_item=menu_item,
            is_primary_recipe=True
        ).update(is_primary_recipe=False)
    
    # Create or update the link
    link, created = RecipeMenuItemLink.objects.update_or_create(
        recipe=recipe,
        menu_item=menu_item,
        defaults={
            'is_primary_recipe': is_primary,
            'auto_created': False,
            'created_by': request.user
        }
    )
    
    if created:
        message = f'Successfully linked "{recipe.name}" to "{menu_item.name}"'
    else:
        message = f'Updated link between "{recipe.name}" and "{menu_item.name}"'
    
    return JsonResponse({
        'success': True,
        'message': message,
        'link_id': link.id
    })

@login_required
@require_POST
def unlink_recipe_from_menu_item(request, link_id):
    """Remove the link between a recipe and menu item"""
    
    link = get_object_or_404(RecipeMenuItemLink, id=link_id)
    recipe_name = link.recipe.name
    menu_item_name = link.menu_item.name
    
    link.delete()
    
    return JsonResponse({
        'success': True,
        'message': f'Successfully unlinked "{recipe_name}" from "{menu_item_name}"'
    })

@login_required
def create_recipe_from_menu_item(request, menu_item_id):
    """Create a new recipe from an existing menu item"""
    
    menu_item = get_object_or_404(MenuItem, id=menu_item_id)
    
    if request.method == 'POST':
        name = request.POST.get('name', f"Recipe for {menu_item.name}")
        description = request.POST.get('description', menu_item.description)
        instructions = request.POST.get('instructions', '')
        prep_time = request.POST.get('prep_time', 15)
        cook_time = request.POST.get('cook_time', 20)
        portions = request.POST.get('portions', 1)
        
        recipe = Recipe.objects.create(
            name=name,
            description=description,
            instructions=instructions,
            prep_time=prep_time,
            cook_time=cook_time,
            total_time=int(prep_time) + int(cook_time),
            portions=portions,
            created_by=request.user
        )
        
        # Auto-link to the menu item
        RecipeMenuItemLink.objects.create(
            recipe=recipe,
            menu_item=menu_item,
            is_primary_recipe=True,
            auto_created=False,
            created_by=request.user
        )
        
        messages.success(request, f'Recipe "{name}" created and linked to "{menu_item.name}"')
        return redirect('recipe_detail', recipe_id=recipe.id)
    
    return render(request, 'menu_management/create_recipe_from_menu_item.html', {
        'menu_item': menu_item
    })

@login_required
def recipe_analytics(request):
    """Analytics view for recipe performance and usage"""
    
    # Recipe usage statistics
    recipe_usage = Recipe.objects.annotate(
        usage_count=Count('menu_item_links__menu_item__orderitem'),
        total_revenue=Sum('menu_item_links__menu_item__orderitem__price')
    ).order_by('-usage_count')
    
    # Most expensive recipes
    expensive_recipes = Recipe.objects.annotate(
        total_ingredient_cost=Sum('ingredients__ingredient__cost_per_unit')
    ).order_by('-total_ingredient_cost')[:10]
    
    # Recipes with most versions
    versioned_recipes = Recipe.objects.annotate(
        version_count=Count('versions')
    ).order_by('-version_count')[:10]
    
    # Unlinked menu items
    unlinked_items = MenuItem.objects.filter(recipe_links__isnull=True).select_related('category')
    
    context = {
        'recipe_usage': recipe_usage[:20],
        'expensive_recipes': expensive_recipes,
        'versioned_recipes': versioned_recipes,
        'unlinked_items': unlinked_items,
    }
    
    return render(request, 'menu_management/recipe_analytics.html', context)

@login_required
@require_POST
def bulk_update_recipe_status(request):
    """Bulk update recipe active/inactive status"""
    
    recipe_ids = request.POST.getlist('recipe_ids')
    action = request.POST.get('action')  # 'activate' or 'deactivate'
    
    if action == 'activate':
        updated = Recipe.objects.filter(id__in=recipe_ids).update(is_active=True)
        message = f'Activated {updated} recipes'
    elif action == 'deactivate':
        updated = Recipe.objects.filter(id__in=recipe_ids).update(is_active=False)
        message = f'Deactivated {updated} recipes'
    else:
        return JsonResponse({'success': False, 'message': 'Invalid action'})
    
    return JsonResponse({
        'success': True,
        'message': message,
        'updated_count': updated
    })
