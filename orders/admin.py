from django.contrib import admin
from .models import Category, MenuItem, Order, OrderItem, MealPass, MealPassSubscription, MealPassSelection


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['price']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'available', 'preparation_time']
    list_filter = ['category', 'available']
    search_fields = ['name', 'description']
    list_editable = ['available', 'preparation_time']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer_name', 'table_number', 'status', 'payment_method', 'total_amount', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'customer_name', 'table_number']
    readonly_fields = ['order_number', 'total_amount', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status in ['completed', 'cancelled']:
            return self.readonly_fields + ['customer_name', 'customer_phone', 'table_number', 'notes']
        return self.readonly_fields


@admin.register(MealPass)
class MealPassAdmin(admin.ModelAdmin):
    list_display = ['name', 'tier', 'price', 'duration_days', 'meals_per_period', 'is_active']
    list_filter = ['tier', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active']


@admin.register(MealPassSubscription)
class MealPassSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'meal_pass', 'start_date', 'end_date', 'status', 'payment_method', 'meals_remaining', 'total_meals', 'created_at']
    list_filter = ['status', 'payment_method', 'meal_pass__tier']
    search_fields = ['user__username', 'user__email', 'meal_pass__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(MealPassSelection)
class MealPassSelectionAdmin(admin.ModelAdmin):
    list_display = ['user', 'subscription', 'selected_meal', 'selection_date', 'created_at']
    list_filter = ['selection_date', 'subscription__meal_pass__tier']
    search_fields = ['user__username', 'selected_meal__name']
    readonly_fields = ['created_at']
