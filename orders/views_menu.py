from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models_menu import *
from .models import MenuItem, Category
from decimal import Decimal
import json

def is_admin(user):
    return user.is_authenticated and user.is_superuser

@login_required
@user_passes_test(is_admin)
def menu_management_dashboard(request):
    """Main menu management dashboard"""
    # Get statistics
    total_recipes = Recipe.objects.count()
    total_ingredients = Ingredient.objects.count()
    active_menus = Menu.objects.filter(is_active=True).count()
    total_menu_items = RecipeMenuItem.objects.count()
    
    # Recent activity
    recent_recipes = Recipe.objects.order_by('-created_at')[:5]
    recent_menu_items = RecipeMenuItem.objects.order_by('-created_at')[:5]
    
    context = {
        'total_recipes': total_recipes,
        'total_ingredients': total_ingredients,
        'active_menus': active_menus,
        'total_menu_items': total_menu_items,
        'recent_recipes': recent_recipes,
        'recent_menu_items': recent_menu_items,
    }
    return render(request, 'menu_management/dashboard.html', context)

# Recipe Management Views
@login_required
@user_passes_test(is_admin)
def recipe_list(request):
    """List all recipes"""
    recipes = Recipe.objects.select_related('created_by').all()
    
    # Filter
    search = request.GET.get('search', '')
    difficulty = request.GET.get('difficulty', '')
    
    if search:
        recipes = recipes.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    if difficulty:
        recipes = recipes.filter(difficulty=difficulty)
    
    # Pagination
    paginator = Paginator(recipes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'difficulty': difficulty,
    }
    return render(request, 'menu_management/recipe_list.html', context)

@login_required
@user_passes_test(is_admin)
def recipe_create(request):
    """Create new recipe"""
    if request.method == 'POST':
        # Create recipe
        recipe = Recipe.objects.create(
            name=request.POST['name'],
            description=request.POST['description'],
            instructions=request.POST['instructions'],
            prep_time=int(request.POST['prep_time']),
            cook_time=int(request.POST['cook_time']),
            total_time=int(request.POST['total_time']),
            difficulty=int(request.POST['difficulty']),
            portions=int(request.POST['portions']),
            chef_notes=request.POST.get('chef_notes', ''),
            equipment_needed=request.POST.get('equipment_needed', ''),
            temperature_specs=request.POST.get('temperature_specs', ''),
            nutritional_info=json.loads(request.POST.get('nutritional_info', '{}')),
            allergen_info=request.POST.get('allergen_info', ''),
            created_by=request.user
        )
        
        # Add ingredients
        ingredient_names = request.POST.getlist('ingredient_name')
        ingredient_quantities = request.POST.getlist('ingredient_quantity')
        ingredient_units = request.POST.getlist('ingredient_unit')
        
        for i, name in enumerate(ingredient_names):
            if name and i < len(ingredient_quantities):
                ingredient = get_object_or_404(Ingredient, name=name)
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ingredient,
                    quantity=ingredient_quantities[i],
                    unit=ingredient_units[i]
                )
        
        # Calculate cost
        total_cost = Decimal('0.00')
        for recipe_ingredient in recipe.ingredients.all():
            ingredient_cost = recipe_ingredient.ingredient.current_price * recipe_ingredient.quantity
            total_cost += ingredient_cost
        
        recipe.cost_per_portion = total_cost / recipe.portions
        recipe.save()
        
        messages.success(request, f'Recipe "{recipe.name}" created successfully!')
        return redirect('menu_management:recipe_detail', recipe.id)
    
    ingredients = Ingredient.objects.filter(is_active=True)
    return render(request, 'menu_management/recipe_create.html', {'ingredients': ingredients})

@login_required
@user_passes_test(is_admin)
def recipe_detail(request, recipe_id):
    """Recipe detail view"""
    recipe = get_object_or_404(Recipe, id=recipe_id)
    versions = recipe.versions.all().order_by('-version_number')
    
    # Calculate current cost
    total_cost = Decimal('0.00')
    for recipe_ingredient in recipe.ingredients.all():
        ingredient_cost = recipe_ingredient.ingredient.current_price * recipe_ingredient.quantity
        total_cost += ingredient_cost
    
    context = {
        'recipe': recipe,
        'versions': versions,
        'total_cost': total_cost,
        'cost_per_portion': total_cost / recipe.portions if recipe.portions > 0 else 0,
    }
    return render(request, 'menu_management/recipe_detail.html', context)

@login_required
@user_passes_test(is_admin)
def recipe_update(request, recipe_id):
    """Update recipe"""
    recipe = get_object_or_404(Recipe, id=recipe_id)
    
    if request.method == 'POST':
        recipe.name = request.POST['name']
        recipe.description = request.POST['description']
        recipe.instructions = request.POST['instructions']
        recipe.prep_time = int(request.POST['prep_time'])
        recipe.cook_time = int(request.POST['cook_time'])
        recipe.total_time = int(request.POST['total_time'])
        recipe.difficulty = int(request.POST['difficulty'])
        recipe.portions = int(request.POST['portions'])
        recipe.chef_notes = request.POST.get('chef_notes', '')
        recipe.equipment_needed = request.POST.get('equipment_needed', '')
        recipe.temperature_specs = request.POST.get('temperature_specs', '')
        recipe.nutritional_info = json.loads(request.POST.get('nutritional_info', '{}'))
        recipe.allergen_info = request.POST.get('allergen_info', '')
        recipe.save()
        
        # Update ingredients
        recipe.ingredients.all().delete()
        ingredient_names = request.POST.getlist('ingredient_name')
        ingredient_quantities = request.POST.getlist('ingredient_quantity')
        ingredient_units = request.POST.getlist('ingredient_unit')
        
        for i, name in enumerate(ingredient_names):
            if name and i < len(ingredient_quantities):
                ingredient = get_object_or_404(Ingredient, name=name)
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ingredient,
                    quantity=ingredient_quantities[i],
                    unit=ingredient_units[i]
                )
        
        # Recalculate cost
        total_cost = Decimal('0.00')
        for recipe_ingredient in recipe.ingredients.all():
            ingredient_cost = recipe_ingredient.ingredient.current_price * recipe_ingredient.quantity
            total_cost += ingredient_cost
        
        recipe.cost_per_portion = total_cost / recipe.portions
        recipe.save()
        
        messages.success(request, f'Recipe "{recipe.name}" updated successfully!')
        return redirect('menu_management:recipe_detail', recipe.id)
    
    ingredients = Ingredient.objects.filter(is_active=True)
    return render(request, 'menu_management/recipe_update.html', {
        'recipe': recipe,
        'ingredients': ingredients
    })

# Menu Engineering Views
@login_required
@user_passes_test(is_admin)
def menu_list(request):
    """List all menus"""
    menus = Menu.objects.select_related('created_by').all()
    
    # Filter
    menu_type = request.GET.get('menu_type', '')
    status = request.GET.get('status', '')
    
    if menu_type:
        menus = menus.filter(menu_type=menu_type)
    
    if status == 'active':
        menus = menus.filter(is_active=True)
    elif status == 'inactive':
        menus = menus.filter(is_active=False)
    
    context = {
        'menus': menus,
        'menu_type': menu_type,
        'status': status,
    }
    return render(request, 'menu_management/menu_list.html', context)

@login_required
@user_passes_test(is_admin)
def menu_create(request):
    """Create new menu"""
    if request.method == 'POST':
        menu = Menu.objects.create(
            name=request.POST['name'],
            menu_type=request.POST['menu_type'],
            description=request.POST.get('description', ''),
            start_date=request.POST.get('start_date') or None,
            end_date=request.POST.get('end_date') or None,
            created_by=request.user
        )
        
        messages.success(request, f'Menu "{menu.name}" created successfully!')
        return redirect('menu_management:menu_detail', menu.id)
    
    return render(request, 'menu_management/menu_create.html')

@login_required
@user_passes_test(is_admin)
def menu_detail(request, menu_id):
    """Menu detail view"""
    menu = get_object_or_404(Menu, id=menu_id)
    sections = menu.sections.all().prefetch_related('items__recipe').order_by('order')
    
    # Calculate menu statistics
    total_items = RecipeMenuItem.objects.filter(menu_section__menu=menu).count()
    total_revenue = MenuPricing.objects.filter(
        menu_item__menu_section__menu=menu
    ).aggregate(total=Sum('price'))['total'] or 0
    
    context = {
        'menu': menu,
        'sections': sections,
        'total_items': total_items,
        'total_revenue': total_revenue,
    }
    return render(request, 'menu_management/menu_detail.html', context)

@login_required
@user_passes_test(is_admin)
def menu_item_create(request, menu_section_id):
    """Add item to menu section"""
    menu_section = get_object_or_404(MenuSection, id=menu_section_id)
    
    if request.method == 'POST':
        recipe = get_object_or_404(Recipe, id=request.POST['recipe'])
        
        menu_item = RecipeMenuItem.objects.create(
            menu_section=menu_section,
            recipe=recipe,
            name=request.POST['name'],
            description=request.POST['description'],
            price=Decimal(request.POST['price']),
            prep_time=recipe.total_time,
            plating_instructions=request.POST.get('plating_instructions', ''),
            chef_notes=request.POST.get('chef_notes', ''),
            dietary_info=json.loads(request.POST.get('dietary_info', '{}'))
        )
        
        # Create pricing
        MenuPricing.objects.create(
            menu_item=menu_item,
            price=Decimal(request.POST['price']),
            cost=recipe.cost_per_portion or Decimal('0.00'),
            markup_percentage=Decimal('0.00')
        )
        
        messages.success(request, f'Item "{menu_item.name}" added to menu!')
        return redirect('menu_management:menu_detail', menu_section.menu.id)
    
    recipes = Recipe.objects.filter(is_active=True)
    return render(request, 'menu_management/menu_item_create.html', {
        'menu_section': menu_section,
        'recipes': recipes
    })

# Analytics Views
@login_required
@user_passes_test(is_admin)
def menu_analytics(request):
    """Menu analytics dashboard"""
    # Get date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Default to last 30 days
    if not start_date:
        start_date = timezone.now() - timezone.timedelta(days=30)
    if not end_date:
        end_date = timezone.now()
    
    # Get analytics data
    analytics = MenuAnalytics.objects.filter(
        date__range=[start_date, end_date]
    ).select_related('menu_item').order_by('-date')
    
    # Calculate totals
    total_orders = analytics.aggregate(
        total=Sum('orders_count'),
        revenue=Sum('revenue'),
        avg_conversion=Avg('conversion_rate')
    )
    
    # Top performing items
    top_items = analytics.values('menu_item__name').annotate(
        total_orders=Sum('orders_count'),
        total_revenue=Sum('revenue')
    ).order_by('-total_revenue')[:10]
    
    context = {
        'analytics': analytics,
        'total_orders': total_orders['total'] or 0,
        'total_revenue': total_orders['revenue'] or 0,
        'avg_conversion': total_orders['avg_conversion'] or 0,
        'top_items': top_items,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'menu_management/analytics.html', context)

# API Views for AJAX
@login_required
@user_passes_test(is_admin)
def update_ingredient_price(request, ingredient_id):
    """Update ingredient price via AJAX"""
    if request.method == 'POST':
        ingredient = get_object_or_404(Ingredient, id=ingredient_id)
        new_price = Decimal(request.POST.get('price'))
        
        old_price = ingredient.current_price
        ingredient.current_price = new_price
        ingredient.save()
        
        # Update all recipe costs that use this ingredient
        for recipe_ingredient in ingredient.recipeingredient_set.all():
            recipe = recipe_ingredient.recipe
            total_cost = Decimal('0.00')
            for ing in recipe.ingredients.all():
                ingredient_cost = ing.ingredient.current_price * ing.quantity
                total_cost += ingredient_cost
            recipe.cost_per_portion = total_cost / recipe.portions if recipe.portions > 0 else Decimal('0.00')
            recipe.save()
        
        return JsonResponse({
            'success': True,
            'old_price': str(old_price),
            'new_price': str(new_price),
            'recipes_updated': ingredient.recipeingredient_set.count()
        })
    
    return JsonResponse({'success': False})

@login_required
@user_passes_test(is_admin)
def toggle_menu_item_availability(request, item_id):
    """Toggle menu item availability"""
    if request.method == 'POST':
        menu_item = get_object_or_404(RecipeMenuItem, id=item_id)
        menu_item.is_available = not menu_item.is_available
        menu_item.save()
        
        return JsonResponse({
            'success': True,
            'available': menu_item.is_available
        })
    
    return JsonResponse({'success': False})
