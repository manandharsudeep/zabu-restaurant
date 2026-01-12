from django.urls import path
from . import views

app_name = 'customer'

urlpatterns = [
    # Course Menu
    path('course-menu/', views.customer_course_menu, name='course_menu'),
    
    # Cart Management
    path('cart/', views.view_cart, name='cart'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/', views.update_cart, name='update_cart'),
    
    # Checkout
    path('checkout/', views.checkout, name='checkout'),
    path('place-order/', views.place_order, name='place_order'),
    
    # Order Confirmation
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
]
