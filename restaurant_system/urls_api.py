from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from orders.api_views import OrderViewSet, OrderItemViewSet

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'orders', OrderViewSet)
router.register(r'order-items', OrderItemViewSet)

# Wire up our API using automatic URL routing
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('', include('orders.urls')),
    path('menu-management/', include('menu_management.urls')),
]
