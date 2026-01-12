from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Avg, Count
from .routing_models import KitchenStation, OrderRouting, StationPerformance
from .routing_service import SmartRoutingService
from orders.models import Order
import json

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
@user_passes_test(is_admin)
def station_management(request):
    """Station management dashboard"""
    routing_service = SmartRoutingService()
    station_status = routing_service.get_station_status()
    
    # Get overall statistics
    total_stations = KitchenStation.objects.count()
    active_stations = KitchenStation.objects.filter(is_active=True).count()
    total_orders = OrderRouting.objects.filter(status__in=['assigned', 'started']).count()
    
    context = {
        'station_status': station_status,
        'total_stations': total_stations,
        'active_stations': active_stations,
        'total_orders': total_orders,
    }
    return render(request, 'menu_management/station_management.html', context)

@login_required
@user_passes_test(is_admin)
def create_station(request):
    """Create new kitchen station"""
    if request.method == 'POST':
        try:
            # Parse JSON data from request body
            import json
            data = json.loads(request.body)
            
            station = KitchenStation.objects.create(
                name=data['name'],
                station_type=data['station_type'],
                capacity=int(data['capacity']),
                avg_preparation_time=int(data['avg_preparation_time']),
                equipment=data.get('equipment', []),
                capabilities=data.get('capabilities', []),
            )
            
            return JsonResponse({
                'success': True,
                'station_id': station.id,
                'message': f'Station "{station.name}" created successfully'
            })
        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False,
                'message': f'Invalid JSON data: {str(e)}'
            })
        except KeyError as e:
            return JsonResponse({
                'success': False,
                'message': f'Missing required field: {str(e)}'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error creating station: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_admin)
def update_station(request, station_id):
    """Update kitchen station"""
    station = get_object_or_404(KitchenStation, id=station_id)
    
    if request.method == 'POST':
        try:
            # Parse JSON data from request body
            import json
            data = json.loads(request.body)
            
            station.name = data['name']
            station.station_type = data['station_type']
            station.capacity = int(data['capacity'])
            station.avg_preparation_time = int(data['avg_preparation_time'])
            station.equipment = data.get('equipment', [])
            station.capabilities = data.get('capabilities', [])
            station.is_active = data.get('is_active', True)
            station.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Station "{station.name}" updated successfully'
            })
        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False,
                'message': f'Invalid JSON data: {str(e)}'
            })
        except KeyError as e:
            return JsonResponse({
                'success': False,
                'message': f'Missing required field: {str(e)}'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error updating station: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_admin)
def route_order(request, order_id):
    """Manually route an order"""
    order = get_object_or_404(Order, id=order_id)
    routing_service = SmartRoutingService()
    
    success = routing_service.route_order(order)
    
    if success:
        return JsonResponse({
            'success': True,
            'message': f'Order #{order.id} routed successfully'
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Failed to route order'
        })

@login_required
@user_passes_test(is_admin)
def rebalance_orders(request):
    """Rebalance orders across stations"""
    routing_service = SmartRoutingService()
    success = routing_service.rebalance_orders()
    
    if success:
        return JsonResponse({
            'success': True,
            'message': 'Orders rebalanced successfully'
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Failed to rebalance orders'
        })

@login_required
@user_passes_test(is_admin)
def optimize_stations(request):
    """Optimize station performance"""
    try:
        routing_service = SmartRoutingService()
        
        # Check if there are any stations
        if not routing_service.stations.exists():
            return JsonResponse({
                'success': False,
                'message': 'No active stations found to optimize'
            })
        
        # Check if there are any recent order routings
        from .routing_models import OrderRouting
        recent_routings_count = OrderRouting.objects.filter(
            completed_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()
        
        if recent_routings_count == 0:
            return JsonResponse({
                'success': False,
                'message': 'No recent order data available for optimization (need at least 7 days of data)'
            })
        
        success = routing_service.optimize_station_performance()
        
        if success:
            return JsonResponse({
                'success': True,
                'message': f'Station performance optimized successfully for {routing_service.stations.count()} stations using {recent_routings_count} recent order routings'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to optimize stations - please check logs for details'
            })
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in optimize_stations: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error optimizing stations: {str(e)}'
        })

@login_required
@user_passes_test(is_admin)
def station_detail(request, station_id):
    """Detailed view of a station"""
    station = get_object_or_404(KitchenStation, id=station_id)
    
    # Check if request wants JSON response (for AJAX calls)
    if request.META.get('HTTP_ACCEPT') == 'application/json' or request.path.endswith(f'/{station_id}/'):
        # Return JSON response for AJAX requests
        return JsonResponse({
            'id': station.id,
            'name': station.name,
            'station_type': station.station_type,
            'capacity': station.capacity,
            'current_load': station.current_load,
            'efficiency_score': station.efficiency_score,
            'avg_preparation_time': station.avg_preparation_time,
            'is_active': station.is_active,
            'equipment': station.equipment,
            'capabilities': station.capabilities,
            'created_at': station.created_at.isoformat(),
            'updated_at': station.updated_at.isoformat(),
        })
    
    # Get active orders for this station
    active_orders = OrderRouting.objects.filter(
        station=station,
        status__in=['assigned', 'started']
    ).select_related('order').order_by('assigned_at')
    
    # Get performance data
    performance_data = StationPerformance.objects.filter(
        station=station
    ).order_by('-date')[:30]  # Last 30 days
    
    # Calculate statistics
    total_orders = OrderRouting.objects.filter(station=station).count()
    avg_time = OrderRouting.objects.filter(
        station=station,
        completed_at__isnull=False
    ).aggregate(avg_time=Avg('time_taken'))['avg_time'] or 0
    
    context = {
        'station': station,
        'active_orders': active_orders,
        'performance_data': performance_data,
        'total_orders': total_orders,
        'avg_time': avg_time,
    }
    return render(request, 'menu_management/station_detail.html', context)

@login_required
@user_passes_test(is_admin)
def update_routing_status(request, routing_id):
    """Update routing status"""
    routing = get_object_or_404(OrderRouting, id=routing_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_statuses = ['pending', 'assigned', 'started', 'completed']
        
        if new_status in valid_statuses:
            routing.status = new_status
            
            if new_status == 'started' and not routing.started_at:
                routing.started_at = timezone.now()
            elif new_status == 'completed' and not routing.completed_at:
                routing.completed_at = timezone.now()
                
                # Update station load
                station = routing.station
                station.current_load = max(0, station.current_load - 1)
                station.save()
            
            routing.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Routing status updated to {new_status}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})
