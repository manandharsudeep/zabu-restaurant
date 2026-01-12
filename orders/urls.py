from django.urls import path, include
from . import views
from . import customer_views
from . import reservation_views
from . import meal_pass_views
from . import order_views
from . import kitchen_views
from . import user_management_views
from . import admin_views
from . import frontend_user_views

urlpatterns = [
    path('', views.gateway_view, name='gateway'),
    path('staff/', views.staff_portal_view, name='staff_portal'),
    path('staff/login/', views.staff_login, name='staff_login'),
    path('staff/logout/', views.staff_logout, name='staff_logout'),
    path('customer/signup/', views.customer_signup, name='customer_signup'),
    path('customer/login/', views.customer_login, name='customer_login'),
    path('customer/logout/', views.customer_logout, name='customer_logout'),
    path('menu/', views.menu_view, name='menu'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order-status/', views.order_status, name='order_status'),
    path('kitchen/', views.kitchen_display, name='kitchen_display'),
    path('kitchen/update/<int:order_id>/<str:new_status>/', views.update_order_status, name='update_order_status'),
    
    # Order Management URLs
    path('orders/dashboard/', order_views.order_dashboard, name='order_dashboard'),
    path('orders/list/', order_views.order_list, name='order_list'),
    path('orders/detail/<int:order_id>/', order_views.order_detail, name='order_detail'),
    path('orders/update-status/<int:order_id>/', order_views.update_order_status, name='update_order_status'),
    path('orders/assign/<int:order_id>/', order_views.assign_order, name='assign_order'),
    path('orders/set-priority/<int:order_id>/', order_views.set_order_priority, name='set_order_priority'),
    path('orders/set-time/<int:order_id>/', order_views.set_estimated_time, name='set_estimated_time'),
    path('orders/statistics/', order_views.order_statistics, name='order_statistics'),
    
    # Kitchen URLs
    path('orders/kitchen/', kitchen_views.kitchen_dashboard, name='kitchen_dashboard'),
    path('orders/kitchen/detail/<int:order_id>/', kitchen_views.kitchen_order_detail, name='kitchen_order_detail'),
    path('orders/kitchen/start-preparation/<int:order_id>/', kitchen_views.start_preparation, name='start_preparation'),
    path('orders/kitchen/mark-ready/<int:order_id>/', kitchen_views.mark_ready, name='mark_ready'),
    path('orders/kitchen/complete/<int:order_id>/', kitchen_views.complete_order, name='complete_order'),
    path('orders/kitchen/queue/', kitchen_views.kitchen_queue, name='kitchen_queue'),
    path('orders/kitchen/add-note/<int:order_id>/', kitchen_views.add_order_note, name='add_order_note'),
    
    # Customer Management URLs
    path('customers/', customer_views.customer_management, name='customer_management'),
    path('customers/<int:customer_id>/', customer_views.customer_detail, name='customer_detail'),
    path('customers/analytics/', customer_views.customer_analytics, name='customer_analytics'),
    path('customers/<int:customer_id>/toggle-status/', customer_views.toggle_customer_status, name='toggle_customer_status'),
    path('customers/export/', customer_views.export_customers, name='export_customers'),
    
    # Reservation URLs
    path('reservations/', reservation_views.reservation_dashboard, name='reservation_dashboard'),
    path('reservations/table/', reservation_views.create_table_reservation, name='create_table_reservation'),
    path('reservations/venue/', reservation_views.create_venue_reservation, name='create_venue_reservation'),
    path('reservations/cancel/<str:reservation_type>/<uuid:reservation_id>/', reservation_views.cancel_reservation, name='cancel_reservation'),
    path('reservations/<str:reservation_type>/<uuid:reservation_id>/', reservation_views.reservation_detail, name='reservation_detail'),
    
    # Meal Pass URLs
    path('meal-pass/', meal_pass_views.meal_pass_options, name='meal_pass_options'),
    path('meal-pass/billing/<uuid:pass_id>/', meal_pass_views.meal_pass_billing, name='meal_pass_billing'),
    path('meal-pass/purchase/<uuid:pass_id>/', meal_pass_views.purchase_meal_pass, name='purchase_meal_pass'),
    path('meal-pass/dashboard/', meal_pass_views.meal_pass_dashboard, name='meal_pass_dashboard'),
    path('meal-pass/use/', meal_pass_views.use_meal_pass, name='use_meal_pass'),
    path('meal-pass/benefits/', meal_pass_views.meal_pass_benefits, name='meal_pass_benefits'),
    path('meal-pass/select/<str:date_str>/', meal_pass_views.daily_meal_selection, name='daily_meal_selection'),
    path('meal-pass/select/', meal_pass_views.daily_meal_selection, name='daily_meal_selection_today'),
    path('meal-pass/select-meal/', meal_pass_views.select_daily_meal, name='select_daily_meal'),
    path('api/meal-pass/check/', meal_pass_views.check_meal_pass_availability, name='check_meal_pass_availability'),
    
    # User Management / Account Management URLs
    path('account/', user_management_views.user_management_dashboard, name='user_management_dashboard'),
    path('account/users/', user_management_views.user_management_dashboard, name='user_management_dashboard'),
    path('account/users/<int:user_id>/', user_management_views.user_details, name='user_details'),
    path('account/users/<int:user_id>/edit/', user_management_views.edit_user, name='edit_user'),
    path('account/users/<int:user_id>/password/', user_management_views.change_user_password, name='change_user_password'),
    path('account/users/create/', user_management_views.create_user, name='create_user'),
    path('account/users/<int:user_id>/delete/', user_management_views.delete_user, name='delete_user'),
    path('account/users/<int:user_id>/toggle/', user_management_views.toggle_user_status, name='toggle_user_status'),
    path('account/api/users/<int:user_id>/update/', user_management_views.update_user_details, name='update_user_details'),
    
    # Profile Management (Self-service)
    path('profile/', user_management_views.my_profile, name='my_profile'),
    path('account/profile/', user_management_views.my_profile, name='my_profile_account'),
    path('profile/password/', user_management_views.change_my_password, name='change_my_password'),
    path('account/profile/password/', user_management_views.change_my_password, name='change_my_password_account'),
    
    # Admin Profile
    path('admin/profile/', admin_views.admin_profile, name='admin_profile'),
    
    # Frontend User Management
    path('admin/users/', frontend_user_views.user_management_frontend, name='user_management_frontend'),
    path('admin/users/create/', frontend_user_views.create_user_frontend, name='create_user_frontend'),
    path('admin/users/<int:user_id>/update/', frontend_user_views.update_user_frontend, name='update_user_frontend'),
    path('admin/users/<int:user_id>/delete/', frontend_user_views.delete_user_frontend, name='delete_user_frontend'),
    path('admin/users/<int:user_id>/password/', frontend_user_views.change_password_frontend, name='change_password_frontend'),
    path('admin/users/<int:user_id>/toggle/', frontend_user_views.toggle_user_status_frontend, name='toggle_user_status_frontend'),
]
