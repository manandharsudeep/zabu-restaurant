from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer

class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows orders to be viewed or edited.
    """
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update order status"""
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status in ['pending', 'confirmed', 'preparing', 'ready', 'completed', 'cancelled']:
            order.status = new_status
            order.save()
            return Response({'status': 'success', 'message': f'Order status updated to {new_status}'})
        else:
            return Response({'status': 'error', 'message': 'Invalid status'}, status=400)

    @action(detail=True, methods=['post'])
    def assign_order(self, request, pk=None):
        """Assign order to staff"""
        order = self.get_object()
        staff_id = request.data.get('staff_id')
        
        if staff_id:
            order.assigned_to_id = staff_id
            order.save()
            return Response({'status': 'success', 'message': 'Order assigned successfully'})
        else:
            return Response({'status': 'error', 'message': 'Staff ID required'}, status=400)

class OrderItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows order items to be viewed or edited.
    """
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]
