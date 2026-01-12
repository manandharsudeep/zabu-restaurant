"""
URL configuration for restaurant_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import global_search

urlpatterns = [
    path("admin/", admin.site.urls),
    path("menu-management/", include("menu_management.urls")),
    path("", include("orders.urls")),
    path("customer/", include("customer.urls")),
    
    # Global Search (Universal across all apps)
    path("search/", global_search.global_search, name="global_search"),
    path("search/suggestions/", global_search.global_search_suggestions, name="global_search_suggestions"),
    path("search/page/", global_search.global_search_page, name="global_search_page"),
]
