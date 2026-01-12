from rest_framework import serializers
from .models import Order, OrderItem, MenuItem

class OrderItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_price = serializers.DecimalField(source='item.price', read_only=True, max_digits=10, decimal_places=2)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'item', 'item_name', 'item_price', 'quantity', 'subtotal']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    time_elapsed = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer_name', 'customer_phone', 'table_number',
            'status', 'priority', 'total_amount', 'created_at', 'updated_at',
            'notes', 'estimated_time', 'assigned_to', 'time_elapsed', 'is_overdue', 'items'
        ]
        read_only_fields = ['order_number', 'created_at', 'updated_at']
