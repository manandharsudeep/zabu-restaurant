from django.urls import path
from . import views_menu

app_name = 'menu_management'

urlpatterns = [
    # Dashboard
    path('', views_menu.menu_management_dashboard, name='dashboard'),
    
    # Recipe Management
    path('recipes/', views_menu.recipe_list, name='recipe_list'),
    path('recipes/create/', views_menu.recipe_create, name='recipe_create'),
    path('recipes/<int:recipe_id>/', views_menu.recipe_detail, name='recipe_detail'),
    path('recipes/<int:recipe_id>/update/', views_menu.recipe_update, name='recipe_update'),
    
    # Menu Engineering
    path('menus/', views_menu.menu_list, name='menu_list'),
    path('menus/create/', views_menu.menu_create, name='menu_create'),
    path('menus/<int:menu_id>/', views_menu.menu_detail, name='menu_detail'),
    path('menus/sections/<int:menu_section_id>/items/create/', views_menu.menu_item_create, name='menu_item_create'),
    
    # Analytics
    path('analytics/', views_menu.menu_analytics, name='analytics'),
    
    # API Endpoints
    path('api/ingredients/<int:ingredient_id>/update-price/', views_menu.update_ingredient_price, name='update_ingredient_price'),
    path('api/menu-items/<int:item_id>/toggle-availability/', views_menu.toggle_menu_item_availability, name='toggle_menu_item_availability'),
]
