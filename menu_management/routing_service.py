from django.utils import timezone
from django.db.models import Avg, Count, Q
from decimal import Decimal
from .routing_models import KitchenStation, OrderRouting, RoutingRule
from orders.models import Order, OrderItem
from menu_management.models import Recipe, RecipeIngredient
import logging

logger = logging.getLogger(__name__)

class SmartRoutingService:
    """Intelligent order routing service"""
    
    def __init__(self):
        self.stations = KitchenStation.objects.filter(is_active=True)
        self.rules = RoutingRule.objects.filter(is_active=True).order_by('priority')
    
    def route_order(self, order):
        """Route an order to the best available stations"""
        try:
            # Clear existing routing for this order
            OrderRouting.objects.filter(order=order).delete()
            
            # Get order items and their requirements
            order_items = OrderItem.objects.filter(order=order)
            
            # Route each item to appropriate station
            for item in order_items:
                best_station = self._find_best_station_for_item(item)
                if best_station:
                    OrderRouting.objects.create(
                        order=order,
                        station=best_station,
                        routing_score=self._calculate_routing_score(item, best_station),
                        estimated_time=self._estimate_preparation_time(item, best_station),
                        priority=self._calculate_priority(item, order),
                        status='assigned',
                        assigned_at=timezone.now()
                    )
                    
                    # Update station load
                    best_station.current_load += 1
                    best_station.save()
                    
                    logger.info(f"Routed Order #{order.id} item {item.id} to {best_station.name}")
                else:
                    logger.warning(f"No suitable station found for Order #{order.id} item {item.id}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error routing Order #{order.id}: {str(e)}")
            return False
    
    def _find_best_station_for_item(self, item):
        """Find the best station for a specific menu item"""
        suitable_stations = []
        
        for station in self.stations:
            if not station.is_available:
                continue
            
            # Check if station can handle this item
            if self._can_station_handle_item(station, item):
                score = self._calculate_routing_score(item, station)
                suitable_stations.append((station, score))
        
        if not suitable_stations:
            return None
        
        # Sort by score (highest first) and return the best
        suitable_stations.sort(key=lambda x: x[1], reverse=True)
        return suitable_stations[0][0]
    
    def _can_station_handle_item(self, station, item):
        """Check if a station can handle a specific item"""
        # Check station type compatibility
        station_capabilities = station.capabilities or []
        
        # Basic compatibility checks based on station type
        if station.station_type == 'grill' and 'grill' not in station_capabilities:
            station_capabilities.append('grill')
        elif station.station_type == 'fry' and 'fry' not in station_capabilities:
            station_capabilities.append('fry')
        elif station.station_type == 'sauté' and 'sauté' not in station_capabilities:
            station_capabilities.append('sauté')
        elif station.station_type == 'cold' and 'cold' not in station_capabilities:
            station_capabilities.append('cold')
        elif station.station_type == 'pastry' and 'pastry' not in station_capabilities:
            station_capabilities.append('pastry')
        
        # Check if item requires specific equipment
        if hasattr(item, 'item') and hasattr(item.item, 'recipe'):
            recipe = item.item.recipe
            if recipe and recipe.equipment_needed:
                required_equipment = [eq.strip() for eq in recipe.equipment_needed.split(',')]
                station_equipment = station.equipment or []
                
                # Check if station has required equipment
                for req_eq in required_equipment:
                    if req_eq and req_eq not in station_equipment:
                        return False
        
        return True
    
    def _calculate_routing_score(self, item, station):
        """Calculate routing score for item-station pairing"""
        score = 100
        
        # Station load factor (lower load = higher score)
        load_factor = (station.capacity - station.current_load) / station.capacity
        score += load_factor * 20
        
        # Station efficiency factor
        score += (station.efficiency_score / 100) * 15
        
        # Station speed factor (faster = higher score)
        if station.avg_preparation_time > 0:
            speed_factor = max(0, 1 - (station.avg_preparation_time / 30))  # 30 min as baseline
            score += speed_factor * 10
        
        # Staff availability factor
        if station.staff_count > 0:
            staff_factor = min(1, station.staff_count / 2)  # 2 staff as ideal
            score += staff_factor * 5
        
        return min(100, int(score))
    
    def _estimate_preparation_time(self, item, station):
        """Estimate preparation time for item at station"""
        base_time = station.avg_preparation_time
        
        # Adjust based on station efficiency
        efficiency_factor = station.efficiency_score / 100
        estimated_time = base_time / efficiency_factor if efficiency_factor > 0 else base_time
        
        # Adjust based on current load
        load_factor = 1 + (station.current_load / station.capacity) * 0.5
        estimated_time *= load_factor
        
        # Adjust based on item complexity
        if hasattr(item, 'item') and hasattr(item.item, 'recipe'):
            recipe = item.item.recipe
            if recipe:
                complexity_factor = recipe.difficulty / 3  # Normalize to 0-1
                estimated_time *= (1 + complexity_factor * 0.3)
        
        return max(1, int(estimated_time))
    
    def _calculate_priority(self, item, order):
        """Calculate order priority"""
        priority = 5  # Default priority
        
        # Rush orders get higher priority
        if hasattr(order, 'is_rush') and order.is_rush:
            priority += 2
        
        # VIP orders get higher priority
        if hasattr(order, 'is_vip') and order.is_vip:
            priority += 3
        
        # Large orders get lower priority
        total_items = OrderItem.objects.filter(order=order).count()
        if total_items > 10:
            priority -= 1
        
        # Old orders get higher priority
        order_age = (timezone.now() - order.created_at).total_seconds() / 60  # minutes
        if order_age > 30:  # Older than 30 minutes
            priority += 1
        
        return max(1, min(10, priority))
    
    def rebalance_orders(self):
        """Rebalance orders across stations for optimal efficiency"""
        try:
            # Get all pending routings
            pending_routings = OrderRouting.objects.filter(status='pending')
            
            for routing in pending_routings:
                # Check if there's a better station available
                current_station = routing.station
                item = OrderItem.objects.get(order=routing.order, id=routing.id if hasattr(routing, 'item_id') else 1)
                
                best_station = self._find_best_station_for_item(item)
                
                if best_station and best_station != current_station:
                    current_score = self._calculate_routing_score(item, current_station)
                    best_score = self._calculate_routing_score(item, best_station)
                    
                    # Re-route if significantly better (10+ points difference)
                    if best_score > current_score + 10:
                        # Update routing
                        routing.station = best_station
                        routing.routing_score = best_score
                        routing.estimated_time = self._estimate_preparation_time(item, best_station)
                        routing.save()
                        
                        # Update station loads
                        current_station.current_load = max(0, current_station.current_load - 1)
                        current_station.save()
                        
                        best_station.current_load += 1
                        best_station.save()
                        
                        logger.info(f"Re-routed Order #{routing.order.id} from {current_station.name} to {best_station.name}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error rebalancing orders: {str(e)}")
            return False
    
    def get_station_status(self):
        """Get current status of all stations"""
        station_status = []
        
        for station in self.stations:
            # Get active routings for this station
            active_routings = OrderRouting.objects.filter(
                station=station,
                status__in=['assigned', 'started']
            )
            
            # Calculate performance metrics using the time_taken property
            total_time = 0
            completed_routings = active_routings.filter(status='completed')
            
            for routing in completed_routings:
                if routing.time_taken:
                    total_time += routing.time_taken
            
            avg_time = total_time / completed_routings.count() if completed_routings.count() > 0 else 0
            
            station_data = {
                'station': station,
                'current_orders': active_routings.count(),
                'load_percentage': station.load_percentage,
                'efficiency': station.efficiency_score,
                'avg_time': avg_time,
                'is_available': station.is_available,
                'staff_count': station.staff_count,
                'capacity': station.capacity,
            }
            
            station_status.append(station_data)
        
        return station_status
    
    def optimize_station_performance(self):
        """Optimize station performance based on historical data"""
        try:
            stations_updated = 0
            
            for station in self.stations:
                try:
                    # Get recent performance data
                    recent_routings = OrderRouting.objects.filter(
                        station=station,
                        completed_at__gte=timezone.now() - timezone.timedelta(days=7)
                    )
                    
                    if recent_routings.exists():
                        # Calculate new efficiency score using the time_taken property
                        total_time = 0
                        completed_routings = recent_routings.filter(status='completed')
                        
                        for routing in completed_routings:
                            if routing.time_taken:
                                total_time += routing.time_taken
                        
                        avg_time = total_time / completed_routings.count() if completed_routings.count() > 0 else station.avg_preparation_time
                        
                        # Update station efficiency based on performance
                        if avg_time < station.avg_preparation_time * 0.9:
                            station.efficiency_score = min(100, station.efficiency_score + 5)
                        elif avg_time > station.avg_preparation_time * 1.2:
                            station.efficiency_score = max(50, station.efficiency_score - 5)
                        
                        # Update average preparation time
                        station.avg_preparation_time = int(avg_time)
                        station.save()
                        stations_updated += 1
                        
                        logger.info(f"Updated performance metrics for {station.name} (avg_time: {avg_time} min)")
                    else:
                        logger.warning(f"No recent order data found for {station.name}")
                        
                except Exception as station_error:
                    logger.error(f"Error optimizing station {station.name}: {str(station_error)}")
                    continue
            
            if stations_updated > 0:
                logger.info(f"Successfully optimized {stations_updated} stations")
                return True
            else:
                logger.warning("No stations were optimized - no recent order data available")
                return True  # Still return True as no error occurred
                
        except Exception as e:
            logger.error(f"Error optimizing station performance: {str(e)}")
            return False
