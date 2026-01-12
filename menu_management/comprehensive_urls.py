# -*- coding: utf-8 -*-
"""
URL patterns for all phases of restaurant management implementation
"""

from django.urls import path, include
from . import comprehensive_views as views

# Phase 1: POS and Delivery Platform Integration
urlpatterns = [
    # POS Integration
    path('pos-integration/', views.pos_integration_dashboard, name='pos_integration_dashboard'),
    path('api/pos-integration/setup/', views.setup_pos_integration, name='setup_pos_integration'),
    
    # Delivery Platform Integration
    path('delivery-platform/', views.delivery_platform_dashboard, name='delivery_platform_dashboard'),
    path('api/delivery-platform/setup/', views.setup_delivery_platform, name='setup_delivery_platform'),
]

# Phase 2: Real-time Order Management
urlpatterns += [
    # Unified Order Queue
    path('unified-orders/', views.unified_order_queue, name='unified_order_queue'),
    path('api/orders/batch/', views.create_order_batch, name='create_order_batch'),
    
    # Real-time Order Tracking
    path('real-time-orders/', views.real_time_order_dashboard, name='real_time_order_dashboard'),
    path('api/orders/update-status/<uuid:order_id>/', views.update_order_status, name='update_order_status'),
    
    # Special Requests Management
    path('special-requests/', views.special_requests_management, name='special_requests_management'),
    path('api/special-requests/<uuid:request_id>/', views.handle_special_request, name='handle_special_request'),
    
    # VIP Customer Management
    path('vip-customers/', views.vip_customer_management, name='vip_customer_management'),
    path('api/vip-customers/<uuid:customer_id>/', views.update_vip_customer, name='update_vip_customer'),
    
    # Customer Feedback
    path('customer-feedback/', views.customer_feedback_dashboard, name='customer_feedback_dashboard'),
    path('api/customer-feedback/<uuid:feedback_id>/', views.respond_to_feedback, name='respond_to_feedback'),
    
    # Order Prioritization
    path('order-prioritization/', views.order_prioritization_settings, name='order_prioritization_settings'),
    path('api/order-prioritization/create/', views.create_prioritization_rule, name='create_prioritization_rule'),
    
    # Order Batching
    path('order-batching/', views.order_batching_dashboard, name='order_batching_dashboard'),
]

# Phase 3: Advanced Scheduling and Kitchen Optimization
urlpatterns += [
    # Advanced Scheduling
    path('advanced-scheduling/', views.advanced_scheduling_dashboard, name='advanced_scheduling_dashboard'),
    path('api/scheduling/optimization/create/', views.create_schedule_optimization, name='create_schedule_optimization'),
    
    # Kitchen Layout Optimization
    path('kitchen-layout/', views.kitchen_layout_designer, name='kitchen_layout_designer'),
    path('api/kitchen-layout/save/', views.save_kitchen_layout, name='save_kitchen_layout'),
    
    # Packaging Management
    path('packaging-management/', views.packaging_management_dashboard, name='packaging_management_dashboard'),
]

# Phase 4: Multi-Location Cloud Kitchen Network
urlpatterns += [
    # Multi-Location Management
    path('multi-location/', views.multi_location_dashboard, name='multi_location_dashboard'),
    path('api/multi-location/create/', views.create_cloud_kitchen_location, name='create_cloud_kitchen_location'),
    
    # Hub-and-Spoke Operations
    path('hub-and-spoke/', views.hub_and_spoke_operations, name='hub_and_spoke_operations'),
    path('api/hub-and-spoke/central-kitchen/create/', views.create_central_prep_kitchen, name='create_central_prep_kitchen'),
]

# Comprehensive Management Dashboard
urlpatterns += [
    path('comprehensive/', views.comprehensive_management_dashboard, name='comprehensive_management_dashboard'),
]

# Real-time API Endpoints
urlpatterns += [
    path('api/real-time/metrics/', views.get_real_time_metrics, name='get_real_time_metrics'),
    path('api/real-time/order-queue/', views.get_order_queue_status, name='get_order_queue_status'),
]

# Include existing URLs
urlpatterns += [
    # Include existing menu_management URLs
    path('', include('menu_management.urls')),
]
