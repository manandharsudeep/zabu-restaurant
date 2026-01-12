from django.urls import path
from . import views
from . import simple_views
from . import station_views
from . import notification_views
from . import food_safety_views
from . import digital_menu_api
from . import advanced_analytics
from . import inventory_staff_views
from . import kitchen_operations_views
from . import enhanced_course_menu_views
from . import recipe_management_views
from . import task_views
from . import purchase_order_views
from . import intelligent_search_views
from . import public_search_views
from . import vendor_views
from . import menu_item_views

app_name = 'menu_management'

urlpatterns = [
    # Dashboard
    path('', views.menu_management_dashboard, name='dashboard'),
    
    # Intelligent Search
    path('search/', intelligent_search_views.intelligent_search, name='intelligent_search'),
    path('search/suggestions/', intelligent_search_views.search_suggestions, name='search_suggestions'),
    
    # Public Search (no authentication required)
    path('public-search/', public_search_views.public_intelligent_search, name='public_intelligent_search'),
    path('public-search/suggestions/', public_search_views.public_search_suggestions, name='public_search_suggestions'),
    
    # Recipe Management
    path('recipes/', views.recipe_list, name='recipe_list'),
    path('recipes/create/', views.recipe_create, name='recipe_create'),
    path('recipes/<int:recipe_id>/', views.recipe_detail, name='recipe_detail'),
    path('recipes/<int:recipe_id>/update/', views.recipe_update, name='recipe_update'),
    
    # Global Task Management (accessible from main module)
    path('tasks/', task_views.task_dashboard, name='task_dashboard'),
    path('tasks/create/', task_views.create_task, name='create_task'),
    path('tasks/<uuid:task_id>/', task_views.task_detail, name='task_detail'),
    path('tasks/<uuid:task_id>/edit/', task_views.edit_task, name='edit_task'),
    path('tasks/<uuid:task_id>/delete/', task_views.delete_task, name='delete_task'),
    path('tasks/<uuid:task_id>/status/', task_views.update_task_status, name='update_task_status'),
    
    # Comprehensive Recipe Management System
    path('recipe-management/', recipe_management_views.recipe_management_dashboard, name='recipe_management_dashboard'),
    path('recipe-management/<int:recipe_id>/', recipe_management_views.recipe_detail, name='recipe_detail'),
    path('recipe-management/auto-link/', recipe_management_views.auto_link_recipes_to_menu_items, name='auto_link_recipes_to_menu_items'),
    path('recipe-management/link/', recipe_management_views.link_recipe_to_menu_item, name='link_recipe_to_menu_item'),
    path('recipe-management/unlink/<int:link_id>/', recipe_management_views.unlink_recipe_from_menu_item, name='unlink_recipe_from_menu_item'),
    path('recipe-management/create-from-menu/<int:menu_item_id>/', recipe_management_views.create_recipe_from_menu_item, name='create_recipe_from_menu_item'),
    path('recipe-management/analytics/', recipe_management_views.recipe_analytics, name='recipe_analytics'),
    path('recipe-management/bulk-update/', recipe_management_views.bulk_update_recipe_status, name='bulk_update_recipe_status'),
    
    # Menu Management
    path('menus/', views.menu_list, name='menu_list'),
    path('menus/create/', views.menu_create, name='menu_create'),
    path('menus/<int:menu_id>/', views.menu_detail, name='menu_detail'),
    path('menus/<int:menu_id>/update/', views.menu_update, name='menu_update'),
    path('menus/<int:menu_id>/sections/create/', views.section_create, name='section_create'),
    path('menus/sections/<int:menu_section_id>/items/create/', views.menu_item_create, name='menu_item_create'),
    
    # Menu Item Management
    path('menu-items/', menu_item_views.menu_item_list, name='menu_item_list'),
    path('menu-items/create/', menu_item_views.create_menu_item, name='create_menu_item'),
    
    # Station Management
    path('stations/', station_views.station_management, name='station_management'),
    path('stations/create/', station_views.create_station, name='create_station'),
    path('stations/<int:station_id>/', station_views.station_detail, name='station_detail'),
    path('stations/<int:station_id>/update/', station_views.update_station, name='update_station'),
    path('stations/<int:routing_id>/status/', station_views.update_routing_status, name='update_routing_status'),
    path('orders/<int:order_id>/route/', station_views.route_order, name='route_order'),
    path('stations/rebalance/', station_views.rebalance_orders, name='rebalance_orders'),
    path('stations/optimize/', station_views.optimize_stations, name='optimize_stations'),
    
    # Notification Center
    path('notifications/', notification_views.notification_center, name='notification_center'),
    path('notifications/<int:notification_id>/mark-read/', notification_views.mark_notification_read, name='mark_notification_read'),
    path('notifications/<int:notification_id>/details/', notification_views.notification_details, name='notification_details'),
    path('notifications/mark-all-read/', notification_views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/preferences/', notification_views.update_notification_preferences, name='update_preferences'),
    path('notifications/send-test/', notification_views.send_test_notification, name='send_test_notification'),
    path('notifications/count/', notification_views.get_notification_count, name='get_notification_count'),
    
    # Food Safety Management
    path('food-safety/', food_safety_views.food_safety_dashboard, name='food_safety_dashboard'),
    path('food-safety/create-log/', food_safety_views.create_safety_log, name='create_safety_log'),
    path('food-safety/create-temp-log/', food_safety_views.create_temperature_log, name='create_temperature_log'),
    path('food-safety/create-haccp-log/', food_safety_views.create_haccp_log, name='create_haccp_log'),
    path('food-safety/statistics/', food_safety_views.get_safety_statistics, name='get_safety_statistics'),
    
    # Digital Menu Board API
    path('api/digital-menu/', digital_menu_api.digital_menu_board_api, name='digital_menu_board_api'),
    path('api/digital-menu/<int:brand_id>/', digital_menu_api.digital_menu_board_api, name='digital_menu_board_brand'),
    path('api/digital-menu/categories/', digital_menu_api.digital_menu_board_categories, name='digital_menu_board_categories'),
    path('api/digital-menu/item/<int:item_id>/', digital_menu_api.digital_menu_board_item_detail, name='digital_menu_board_item_detail'),
    path('api/digital-menu/update/', digital_menu_api.update_menu_availability, name='update_menu_availability'),
    path('api/digital-menu/status/', digital_menu_api.digital_menu_board_status, name='digital_menu_board_status'),
    path('api/digital-menu/sync/', digital_menu_api.digital_menu_board_sync, name='digital_menu_board_sync'),
    
    # Advanced Analytics
    path('analytics/ab-test/create/', advanced_analytics.create_ab_test, name='create_ab_test'),
    path('analytics/suggestions/', advanced_analytics.menu_optimization_suggestions, name='menu_optimization_suggestions'),
    
    # Digital Menu Board Interface
    path('digital-menu/', advanced_analytics.digital_menu_board_view, name='digital_menu_board'),
    path('menu-display/', advanced_analytics.public_digital_menu_board, name='public_digital_menu'),
    
    # Inventory Management
    path('inventory/', inventory_staff_views.inventory_dashboard, name='inventory_dashboard'),
    path('inventory/items/', inventory_staff_views.inventory_items_list, name='inventory_items'),
    path('inventory/items/create/', inventory_staff_views.create_inventory_item, name='create_inventory_item'),
    path('inventory/vendor/create/', vendor_views.create_vendor, name='create_vendor'),
    path('inventory/transactions/', inventory_staff_views.inventory_transactions, name='inventory_transactions'),
    path('inventory/purchase-orders/', inventory_staff_views.purchase_orders, name='purchase_orders'),
    path('inventory/purchase-orders/create/', purchase_order_views.create_purchase_order, name='create_purchase_order'),
    path('inventory/purchase-orders/<int:po_id>/', purchase_order_views.purchase_order_detail, name='purchase_order_detail'),
    path('inventory/waste/', inventory_staff_views.waste_tracking, name='waste_tracking'),
    path('inventory/reports/', inventory_staff_views.inventory_reports, name='inventory_reports'),
    
    # Staff Management
    path('staff/', inventory_staff_views.staff_dashboard, name='staff_dashboard'),
    path('staff/scheduling/', inventory_staff_views.staff_scheduling, name='staff_scheduling'),
    path('staff/tasks/', inventory_staff_views.task_management, name='task_management'),
    path('staff/tasks/create/', task_views.create_task, name='create_task'),
    path('staff/tasks/<uuid:task_id>/', task_views.task_detail, name='task_detail'),
    path('staff/tasks/<uuid:task_id>/edit/', task_views.edit_task, name='edit_task'),
    path('staff/tasks/<uuid:task_id>/delete/', task_views.delete_task, name='delete_task'),
    path('staff/tasks/<uuid:task_id>/status/', task_views.update_task_status, name='update_task_status'),
    path('staff/communications/', inventory_staff_views.staff_communications, name='staff_communications'),
    path('staff/reports/', inventory_staff_views.staff_reports, name='staff_reports'),
    
    # API Endpoints
    path('api/inventory-levels/', inventory_staff_views.api_inventory_levels, name='api_inventory_levels'),
    path('api/staff-schedule/', inventory_staff_views.api_staff_schedule, name='api_staff_schedule'),
    
    # Kitchen Operations - Order Management
    path('kitchen/', kitchen_operations_views.kitchen_display_system, name='kitchen_display_system'),
    path('kitchen/orders/', kitchen_operations_views.order_management, name='order_management'),
    path('kitchen/orders/<uuid:order_id>/status/', kitchen_operations_views.update_order_status, name='update_order_status'),
    path('kitchen/items/<int:item_id>/fire/', kitchen_operations_views.fire_order_item, name='fire_order_item'),
    
    # Kitchen Operations - Prep Management
    path('kitchen/prep/', kitchen_operations_views.prep_management, name='prep_management'),
    path('kitchen/prep/generate/', kitchen_operations_views.generate_prep_list, name='generate_prep_list'),
    path('kitchen/prep/<uuid:task_id>/update/', kitchen_operations_views.update_prep_task, name='update_prep_task'),
    
    # Kitchen Operations - Cloud Kitchen
    path('kitchen/cloud/', kitchen_operations_views.cloud_kitchen_operations, name='cloud_kitchen_operations'),
    path('kitchen/cloud/batch/', kitchen_operations_views.create_order_batch, name='create_order_batch'),
    path('kitchen/cloud/handoff/<uuid:handoff_id>/', kitchen_operations_views.driver_handoff, name='driver_handoff'),
    
    # Cloud Kitchen Management
    path('kitchen/cloud/brands/', kitchen_operations_views.virtual_brands_management, name='virtual_brands_management'),
    path('kitchen/cloud/brands/create/', kitchen_operations_views.create_virtual_brand, name='create_virtual_brand'),
    path('kitchen/cloud/platforms/', kitchen_operations_views.platform_integrations, name='platform_integrations'),
    path('kitchen/cloud/platforms/add/', kitchen_operations_views.add_platform_integration, name='add_platform_integration'),
    path('kitchen/cloud/orders/', kitchen_operations_views.cloud_order_management, name='cloud_order_management'),
    path('kitchen/cloud/queue/', kitchen_operations_views.order_queue_management, name='order_queue_management'),
    path('kitchen/cloud/stations/', kitchen_operations_views.kitchen_station_monitoring, name='kitchen_station_monitoring'),
    path('kitchen/cloud/inventory/', kitchen_operations_views.cloud_inventory_management, name='cloud_inventory_management'),
    path('kitchen/cloud/analytics/', kitchen_operations_views.cloud_performance_analytics, name='cloud_performance_analytics'),
    
    # Kitchen Operations - Course Coordination
    path('kitchen/courses/', kitchen_operations_views.course_menu_coordination, name='course_menu_coordination'),
    path('kitchen/courses/create/', kitchen_operations_views.create_course_menu, name='create_course_menu'),
    
    # Enhanced Course Menu Management
    path('courses/', enhanced_course_menu_views.enhanced_course_menu_dashboard, name='enhanced_course_menu_dashboard'),
    path('courses/templates/', enhanced_course_menu_views.course_menu_templates, name='course_menu_templates'),
    path('courses/templates/create/', enhanced_course_menu_views.create_course_menu_template, name='create_course_menu_template'),
    path('courses/templates/<uuid:template_id>/', enhanced_course_menu_views.course_menu_template_detail, name='course_menu_template_detail'),
    path('courses/templates/<uuid:template_id>/edit/', enhanced_course_menu_views.edit_course_menu_template, name='edit_course_menu_template'),
    path('courses/templates/<uuid:template_id>/add-course/', enhanced_course_menu_views.add_course_to_template, name='add_course_to_template'),
    path('courses/instances/', enhanced_course_menu_views.course_menu_instances, name='course_menu_instances'),
    path('courses/instances/create/', enhanced_course_menu_views.create_course_menu_instance, name='create_course_menu_instance'),
    path('courses/instances/<uuid:instance_id>/', enhanced_course_menu_views.course_menu_instance_detail, name='course_menu_instance_detail'),
    path('courses/instances/<uuid:instance_id>/status/', enhanced_course_menu_views.update_course_instance_status, name='update_course_instance_status'),
    path('courses/pairings/wine/', enhanced_course_menu_views.wine_pairing_management, name='wine_pairing_management'),
    path('courses/pairings/beverage/', enhanced_course_menu_views.beverage_pairing_management, name='beverage_pairing_management'),
    path('courses/analytics/', enhanced_course_menu_views.course_menu_analytics, name='course_menu_analytics'),
    
    # Kitchen Operations - Food Safety
    path('kitchen/safety/', kitchen_operations_views.food_safety_dashboard, name='food_safety_dashboard'),
    path('kitchen/safety/temperature/', kitchen_operations_views.log_temperature, name='log_temperature'),
    path('kitchen/safety/sanitation/<uuid:checklist_id>/', kitchen_operations_views.complete_sanitation_checklist, name='complete_sanitation_checklist'),
    
    # Kitchen Operations APIs
    path('api/kitchen-orders/', kitchen_operations_views.api_kitchen_orders, name='api_kitchen_orders'),
    path('api/prep-tasks/', kitchen_operations_views.api_prep_tasks, name='api_prep_tasks'),
    
    # Multi-Brand Management
    path('multi-brand/', views.multi_brand_management, name='multi_brand'),
    path('platform-integration/', simple_views.simple_platform_integration, name='platform_integration'),
    path('performance-analytics/', simple_views.simple_performance_analytics, name='performance_analytics'),
    path('menu-optimization/', simple_views.simple_menu_optimization, name='menu_optimization'),
    path('ghost-kitchen/', simple_views.simple_ghost_kitchen, name='ghost_kitchen'),
    path('unified-management/', simple_views.simple_unified_management, name='unified_management'),
    
    # API Endpoints
    path('api/ingredients/<int:ingredient_id>/update-price/', views.update_ingredient_price, name='update_ingredient_price'),
    path('api/menu-items/<int:item_id>/toggle-availability/', views.toggle_menu_item_availability, name='toggle_menu_item_availability'),
    path('api/create-brand/', simple_views.create_simple_brand, name='create_virtual_brand'),
    
    # Order Management
    path('rebalance-orders/', views.rebalance_orders, name='rebalance_orders'),
    
    # Note: User Management moved to orders app for better organization
    
    # Testing API endpoints (no auth required)
    path('api/test/recipes/', views.api_recipes_test, name='api_recipes_test'),
    path('api/test/recipes/<int:recipe_id>/', views.api_recipes_test_detail, name='api_recipes_test_detail'),
    path('api/test/menus/', views.api_menus_test, name='api_menus_test'),
    path('api/test/menus/<int:menu_id>/', views.api_menus_test_detail, name='api_menus_test_detail'),
    path('api/test/stations/', views.api_stations_test, name='api_stations_test'),
    path('api/test/stations/<int:station_id>/', views.api_stations_test_detail, name='api_stations_test_detail'),
    
    # Real Analytics Functions
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('analytics/data/', views.get_analytics_data, name='get_analytics_data'),
    
    # A/B Testing
    path('ab-testing/', views.ab_testing_dashboard, name='ab_testing_dashboard'),
    path('ab-testing/create/', views.create_ab_test, name='create_ab_test'),
    
    # Menu Optimization
    path('menu-optimization/', views.menu_optimization_dashboard, name='menu_optimization_dashboard'),
    path('menu-optimization/create/', views.create_optimization, name='create_optimization'),
    
    # Staff Scheduling API
    path('api/schedule/create/', inventory_staff_views.create_schedule, name='create_schedule'),
    path('api/schedule/<uuid:schedule_id>/', inventory_staff_views.get_schedule_data, name='get_schedule_data'),
    path('api/schedule/<uuid:schedule_id>/update/', inventory_staff_views.update_schedule, name='update_schedule'),
    path('api/schedule/<uuid:schedule_id>/delete/', inventory_staff_views.delete_schedule, name='delete_schedule'),
    path('api/shift-template/<int:template_id>/', inventory_staff_views.get_shift_template_details, name='get_shift_template_details'),
    
    # ============================================
    # COMPREHENSIVE IMPLEMENTATION - ALL PHASES
    # ============================================
    
    # Phase 1: POS and Delivery Platform Integration
    path('pos-integration/', simple_views.pos_integration_dashboard, name='pos_integration_dashboard'),
    path('pos-integration/create/', simple_views.create_pos_integration, name='create_pos_integration'),
    path('api/pos-integration/setup/', simple_views.setup_pos_integration, name='setup_pos_integration'),
    
    path('delivery-platform/', simple_views.delivery_platform_dashboard, name='delivery_platform_dashboard'),
    path('delivery-platform/create/', simple_views.create_delivery_platform, name='create_delivery_platform'),
    path('api/delivery-platform/setup/', simple_views.setup_delivery_platform, name='setup_delivery_platform'),
    
    # Phase 2: Real-time Order Management
    path('unified-orders/', simple_views.unified_order_queue, name='unified_order_queue'),
    path('api/orders/batch/', simple_views.create_order_batch, name='create_order_batch'),
    
    path('real-time-orders/', simple_views.real_time_order_dashboard, name='real_time_order_dashboard'),
    path('api/orders/update-status/<uuid:order_id>/', simple_views.update_order_status, name='update_order_status'),
    
    path('special-requests/', simple_views.special_requests_management, name='special_requests_management'),
    path('api/special-requests/<uuid:request_id>/', simple_views.handle_special_request, name='handle_special_request'),
    
    path('vip-customers/', simple_views.vip_customer_management, name='vip_customer_management'),
    path('api/vip-customers/<uuid:customer_id>/', simple_views.update_vip_customer, name='update_vip_customer'),
    
    path('customer-feedback/', simple_views.customer_feedback_dashboard, name='customer_feedback_dashboard'),
    path('api/customer-feedback/<uuid:feedback_id>/', simple_views.respond_to_feedback, name='respond_to_feedback'),
    
    path('order-prioritization/', simple_views.order_prioritization_settings, name='order_prioritization_settings'),
    path('api/order-prioritization/create/', simple_views.create_prioritization_rule, name='create_prioritization_rule'),
    
    path('order-batching/', simple_views.order_batching_dashboard, name='order_batching_dashboard'),
    
    # Phase 3: Advanced Scheduling and Kitchen Optimization
    path('advanced-scheduling/', simple_views.advanced_scheduling_dashboard, name='advanced_scheduling_dashboard'),
    path('api/scheduling/optimization/create/', simple_views.create_schedule_optimization, name='create_schedule_optimization'),
    
    path('kitchen-layout/', simple_views.kitchen_layout_designer, name='kitchen_layout_designer'),
    path('api/kitchen-layout/save/', simple_views.save_kitchen_layout, name='save_kitchen_layout'),
    
    path('packaging-management/', simple_views.packaging_management_dashboard, name='packaging_management_dashboard'),
    
    # Phase 4: Multi-Location Cloud Kitchen Network
    path('multi-location/', simple_views.multi_location_dashboard, name='multi_location_dashboard'),
    path('api/multi-location/create/', simple_views.create_cloud_kitchen_location, name='create_cloud_kitchen_location'),
    
    path('hub-and-spoke/', simple_views.hub_and_spoke_operations, name='hub_and_spoke_operations'),
    path('api/hub-and-spoke/central-kitchen/create/', simple_views.create_central_prep_kitchen, name='create_central_prep_kitchen'),
    
    # Comprehensive Management Dashboard
    path('comprehensive/', simple_views.comprehensive_management_dashboard, name='comprehensive_management_dashboard'),
    
    # Real-time API Endpoints
    path('api/real-time/metrics/', simple_views.get_real_time_metrics, name='get_real_time_metrics'),
    path('api/real-time/order-queue/', simple_views.get_order_queue_status, name='get_order_queue_status'),
]
