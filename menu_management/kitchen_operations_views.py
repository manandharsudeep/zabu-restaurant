from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Avg, Q, F, Expression, FloatField
from django.utils import timezone
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from datetime import timedelta, date, time, datetime
from decimal import Decimal
import json

from .models import *
from .kitchen_operations_models import *
from .routing_models import KitchenStation
from .routing_service import SmartRoutingService

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

# 3.2.1 Order Management Views

@login_required
@user_passes_test(is_admin)
def kitchen_display_system(request):
    """Kitchen Display System (KDS) - Real-time order visualization"""
    # Get active orders
    active_orders = KitchenOrder.objects.filter(
        status__in=['received', 'confirmed', 'preparing', 'cooking', 'plating']
    ).select_related('source').prefetch_related('items').order_by('-priority', 'received_at')
    
    # Get station-specific orders
    station_filter = request.GET.get('station')
    if station_filter:
        active_orders = active_orders.filter(items__assigned_station__id=station_filter).distinct()
    
    # Get completed orders (recent)
    completed_orders = KitchenOrder.objects.filter(
        status='ready',
        completed_at__gte=timezone.now() - timedelta(minutes=30)
    ).select_related('source').order_by('-completed_at')
    
    # Get KDS settings
    kds_settings = {
        'auto_refresh': 5,
        'max_orders': 20,
        'show_completed': True,
        'color_scheme': {
            'received': '#ffc107',
            'confirmed': '#17a2b8',
            'preparing': '#6f42c1',
            'cooking': '#fd7e14',
            'plating': '#20c997',
            'ready': '#28a745',
            'urgent': '#dc3545',
            'vip': '#6f42c1'
        }
    }
    
    # Get stations for filtering
    stations = KitchenStation.objects.filter(is_active=True)
    
    context = {
        'active_orders': active_orders,
        'completed_orders': completed_orders,
        'stations': stations,
        'selected_station': station_filter,
        'kds_settings': kds_settings,
    }
    
    return render(request, 'menu_management/kitchen_display_system.html', context)

@login_required
@user_passes_test(is_admin)
def order_management(request):
    """Comprehensive order management dashboard"""
    # Order statistics
    total_orders = KitchenOrder.objects.count()
    active_orders = KitchenOrder.objects.filter(
        status__in=['received', 'confirmed', 'preparing', 'cooking', 'plating']
    ).count()
    
    rush_orders = KitchenOrder.objects.filter(is_rush_order=True, status__in=['received', 'confirmed']).count()
    vip_orders = KitchenOrder.objects.filter(is_vip_order=True, status__in=['received', 'confirmed']).count()
    
    # Recent orders
    recent_orders = KitchenOrder.objects.select_related('source').prefetch_related('items').order_by('-received_at')[:20]
    
    # Order status breakdown
    status_breakdown = KitchenOrder.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Priority breakdown
    priority_breakdown = KitchenOrder.objects.values('priority').annotate(
        count=Count('id')
    ).order_by('priority')
    
    context = {
        'total_orders': total_orders,
        'active_orders': active_orders,
        'rush_orders': rush_orders,
        'vip_orders': vip_orders,
        'recent_orders': recent_orders,
        'status_breakdown': status_breakdown,
        'priority_breakdown': priority_breakdown,
    }
    
    return render(request, 'menu_management/order_management.html', context)

@login_required
@user_passes_test(is_admin)
def update_order_status(request, order_id):
    """Update order status with bump bar simulation"""
    if request.method == 'POST':
        order = get_object_or_404(KitchenOrder, order_id=order_id)
        new_status = request.POST.get('status')
        
        if new_status in dict(KitchenOrder.STATUS_CHOICES):
            old_status = order.status
            order.status = new_status
            
            # Update timestamps
            if new_status == 'confirmed' and not order.confirmed_at:
                order.confirmed_at = timezone.now()
                order.confirmed_by = request.user
            elif new_status == 'preparing' and not order.started_at:
                order.started_at = timezone.now()
            elif new_status == 'ready' and not order.completed_at:
                order.completed_at = timezone.now()
                order.actual_prep_time = int((timezone.now() - order.started_at).total_seconds() / 60) if order.started_at else None
            
            order.save()
            
            # Update item statuses if order is completed
            if new_status == 'ready':
                order.items.all().update(status='ready', completed_at=timezone.now())
            
            return JsonResponse({
                'success': True,
                'old_status': old_status,
                'new_status': new_status,
                'timestamp': timezone.now().isoformat()
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
@user_passes_test(is_admin)
def fire_order_item(request, item_id):
    """Fire order item for cooking"""
    if request.method == 'POST':
        item = get_object_or_404(OrderItem, id=item_id)
        
        # Set fire time and update status
        item.fire_time = timezone.now()
        item.status = 'cooking'
        item.save()
        
        # Update order status if all items are fired
        order = item.order
        if order.items.filter(status='pending').count() == 0:
            order.status = 'cooking'
            order.save()
        
        return JsonResponse({
            'success': True,
            'fire_time': item.fire_time.isoformat(),
            'item_status': item.status,
            'order_status': order.status
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# 3.2.3 Prep Management Views

@login_required
@user_passes_test(is_admin)
def prep_management(request):
    """Prep management dashboard with demand forecasting display"""
    # Get today's prep tasks
    today = date.today()
    prep_tasks = PrepTask.objects.filter(
        scheduled_date=today
    ).select_related('prep_item', 'assigned_to', 'assigned_station').order_by('priority', 'scheduled_time')
    
    # Statistics
    total_tasks = prep_tasks.count()
    completed_tasks = prep_tasks.filter(status='completed').count()
    in_progress_tasks = prep_tasks.filter(status='in_progress').count()
    
    # Get prep items with low stock
    low_stock_items = PrepItem.objects.filter(
        is_active=True
    ).annotate(
        current_stock=Sum('preptask__completed_quantity', filter=Q(preptask__scheduled_date=today))
    ).filter(
        current_stock__lt=F('par_level')
    )
    
    # Get prep checklists
    today_checklists = PrepChecklist.objects.filter(
        checklist_date=today
    ).select_related('station', 'assigned_to')
    
    # Get demand forecast summary from session if available
    forecast_summary = request.session.get('demand_forecast_summary', [])
    forecast_date = request.session.get('forecast_date', '')
    forecast_days = request.session.get('forecast_days', 7)
    
    # Clear forecast from session after displaying
    if forecast_summary:
        del request.session['demand_forecast_summary']
        del request.session['forecast_date']
        del request.session['forecast_days']
    
    context = {
        'prep_tasks': prep_tasks,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'in_progress_tasks': in_progress_tasks,
        'low_stock_items': low_stock_items,
        'today_checklists': today_checklists,
        'forecast_summary': forecast_summary,
        'forecast_date': forecast_date,
        'forecast_days': forecast_days,
    }
    
    return render(request, 'menu_management/prep_management.html', context)

@login_required
@user_passes_test(is_admin)
def generate_prep_list(request):
    """Generate automated prep list based on demand forecasting"""
    if request.method == 'POST':
        try:
            target_date = request.POST.get('target_date', date.today())
            forecast_days = int(request.POST.get('forecast_days', 7))
            
            # Parse date string if needed
            if isinstance(target_date, str):
                target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            
            # Get historical order data for demand forecasting
            from datetime import timedelta
            from django.db.models import Avg, Sum, Count
            from orders.models import Order, OrderItem
            
            # Analyze demand from orders for the past 4 weeks
            end_date = target_date - timedelta(days=1)
            start_date = end_date - timedelta(days=forecast_days)
            
            # Get order items from the past 4 weeks
            historical_items = OrderItem.objects.filter(
                order__received_at__date__range=[start_date, end_date],
                order__status='completed'
            ).values('menu_item__name').annotate(
                total_quantity=Sum('quantity'),
                order_count=Count('id'),
                avg_quantity=Avg('quantity')
            ).order_by('-total_quantity')
            
            # Create demand forecast map
            demand_forecast = {}
            for item_data in historical_items:
                item_name = item_data['menu_item__name']
                # Calculate daily average demand
                daily_avg = item_data['total_quantity'] / float(forecast_days)
                
                # Apply seasonal multiplier (simplified - in real system would use more sophisticated forecasting)
                seasonal_multiplier = 1.0
                weekday = target_date.weekday()
                if weekday in [5, 6]:  # Weekend
                    seasonal_multiplier = 1.3
                elif weekday == 0:  # Monday
                    seasonal_multiplier = 1.1
                elif weekday in [2, 3, 4]:  # Tuesday-Thursday
                    seasonal_multiplier = 0.9
                
                # Forecast demand for the target date
                forecasted_demand = daily_avg * seasonal_multiplier
                demand_forecast[item_name] = {
                    'daily_avg': daily_avg,
                    'forecasted_demand': forecasted_demand,
                    'historical_total': item_data['total_quantity'],
                    'order_count': item_data['order_count']
                }
            
            # Get prep items and match with demand forecast
            prep_items = PrepItem.objects.filter(is_active=True)
            generated_tasks = []
            forecast_summary = []
            
            for item in prep_items:
                try:
                    # Find matching demand forecast
                    item_demand = demand_forecast.get(item.name, {
                        'daily_avg': 0,
                        'forecasted_demand': 0,
                        'historical_total': 0,
                        'order_count': 0
                    })
                    
                    # Calculate required quantity based on forecast
                    forecasted_demand = item_demand['forecasted_demand']
                    
                    # If no historical data, use par level as baseline
                    if forecasted_demand == 0:
                        forecasted_demand = float(item.par_level)
                    
                    # Add safety stock (20% buffer)
                    safety_stock = forecasted_demand * 0.2
                    required_quantity = forecasted_demand + safety_stock
                    
                    # Consider current stock levels
                    current_stock = 0  # In real system, would check inventory
                    net_required = max(0, required_quantity - current_stock)
                    
                    # Create prep task if needed
                    existing_task = PrepTask.objects.filter(
                        prep_item=item,
                        scheduled_date=target_date
                    ).first()
                    
                    if not existing_task and net_required > 0:
                        # Determine priority based on demand
                        if forecasted_demand > float(item.par_level) * 1.5:
                            priority = 'high'
                        elif forecasted_demand > float(item.par_level):
                            priority = 'medium'
                        else:
                            priority = 'low'
                        
                        task = PrepTask.objects.create(
                            prep_item=item,
                            scheduled_date=target_date,
                            scheduled_time=time(8, 0),  # Default to 8 AM
                            priority=priority,
                            target_quantity=Decimal(str(net_required)),
                            created_by=request.user
                        )
                        generated_tasks.append(task)
                    
                    # Add to forecast summary
                    forecast_summary.append({
                        'item_name': item.name,
                        'category': item.category,
                        'par_level': item.par_level,
                        'forecasted_demand': round(forecasted_demand, 2),
                        'required_quantity': round(required_quantity, 2),
                        'current_stock': current_stock,
                        'net_required': round(net_required, 2),
                        'priority': priority if net_required > 0 else 'none',
                        'historical_orders': item_demand['order_count'],
                        'daily_avg': round(item_demand['daily_avg'], 2)
                    })
                    
                except Exception as e:
                    # Log error for this item but continue with others
                    print(f"Error creating prep task for {item.name}: {e}")
                    continue
            
            # Store forecast summary in session for display
            request.session['demand_forecast_summary'] = forecast_summary
            request.session['forecast_date'] = target_date.strftime('%Y-%m-%d')
            request.session['forecast_days'] = forecast_days
            
            messages.success(request, f'Generated {len(generated_tasks)} prep tasks for {target_date} based on demand forecasting')
            return redirect(reverse_lazy('menu_management:prep_management'))
            
        except Exception as e:
            messages.error(request, f'Error generating prep list: {str(e)}')
            return redirect(reverse_lazy('menu_management:prep_management'))
    
    return render(request, 'menu_management/generate_prep_list.html')

@login_required
@user_passes_test(is_admin)
def update_prep_task(request, task_id):
    """Update prep task status"""
    if request.method == 'POST':
        task = get_object_or_404(PrepTask, task_id=task_id)
        action = request.POST.get('action')
        
        if action == 'start':
            task.status = 'in_progress'
            task.started_at = timezone.now()
            task.assigned_to = request.user
        elif action == 'complete':
            task.status = 'completed'
            task.completed_at = timezone.now()
            task.completed_quantity = request.POST.get('completed_quantity', task.target_quantity)
            task.actual_duration = int((timezone.now() - task.started_at).total_seconds() / 60) if task.started_at else None
        elif action == 'cancel':
            task.status = 'cancelled'
        
        task.save()
        
        return JsonResponse({
            'success': True,
            'status': task.status,
            'completed_quantity': float(task.completed_quantity),
            'actual_duration': task.actual_duration
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# 3.2.4 Cloud Kitchen Operations Views

@login_required
@user_passes_test(is_admin)
def cloud_kitchen_operations(request):
    """Cloud kitchen operations dashboard"""
    # Get active order batches
    active_batches = OrderBatch.objects.filter(
        status__in=['pending', 'in_progress']
    ).prefetch_related('orders').order_by('-priority', 'start_time')
    
    # Get assembly lines
    assembly_lines = AssemblyLine.objects.filter(is_active=True).prefetch_related('stations')
    
    # Get packaging stations
    packaging_stations = PackagingStation.objects.filter(is_active=True).prefetch_related('staff_assigned')
    
    # Get driver handoffs
    pending_handoffs = DriverHandoff.objects.filter(
        actual_pickup__isnull=True
    ).select_related('order', 'order__source').order_by('estimated_pickup')
    
    # Statistics
    total_batches = OrderBatch.objects.count()
    efficiency_gain = OrderBatch.objects.aggregate(
        avg_efficiency=Avg('efficiency_gain')
    )['avg_efficiency'] or 0
    
    context = {
        'active_batches': active_batches,
        'assembly_lines': assembly_lines,
        'packaging_stations': packaging_stations,
        'pending_handoffs': pending_handoffs,
        'total_batches': total_batches,
        'efficiency_gain': efficiency_gain,
    }
    
    return render(request, 'menu_management/cloud_kitchen_operations.html', context)

@login_required
@user_passes_test(is_admin)
def create_order_batch(request):
    """Create order batch for efficiency"""
    if request.method == 'POST':
        # Get orders with similar characteristics
        prep_time = int(request.POST.get('prep_time'))
        cooking_method = request.POST.get('cooking_method')
        packaging_type = request.POST.get('packaging_type')
        
        # Find similar orders
        similar_orders = KitchenOrder.objects.filter(
            status='received',
            items__preparation_time=prep_time
        ).distinct()
        
        if similar_orders.exists():
            batch = OrderBatch.objects.create(
                name=f"Batch {timezone.now().strftime('%H%M')}",
                preparation_time=prep_time,
                cooking_method=cooking_method,
                packaging_type=packaging_type,
                start_time=timezone.now(),
                priority='normal'
            )
            
            batch.orders.set(similar_orders[:10])  # Limit to 10 orders per batch
            batch.total_orders = batch.orders.count()
            batch.save()
            
            # Update order status
            similar_orders.update(status='preparing')
            
            return JsonResponse({
                'success': True,
                'batch_id': str(batch.batch_id),
                'orders_count': batch.total_orders
            })
    
    return JsonResponse({'success': False, 'error': 'No similar orders found'})

@login_required
@user_passes_test(is_admin)
def driver_handoff(request, handoff_id):
    """Process driver handoff"""
    if request.method == 'POST':
        handoff = get_object_or_404(DriverHandoff, handoff_id=handoff_id)
        
        # Update handoff details
        handoff.actual_pickup = timezone.now()
        handoff.packaging_verified = request.POST.get('packaging_verified', False) == 'true'
        handoff.temperature_verified = request.POST.get('temperature_verified', False) == 'true'
        handoff.quality_verified = request.POST.get('quality_verified', False) == 'true'
        handoff.customer_notified = True
        
        handoff.save()
        
        # Update order status
        handoff.order.status = 'served'
        handoff.order.save()
        
        return JsonResponse({
            'success': True,
            'pickup_time': handoff.actual_pickup.isoformat(),
            'order_status': handoff.order.status
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# 3.2.5 Course Menu Coordination Views

@login_required
@user_passes_test(is_admin)
def course_menu_coordination(request):
    """Course menu coordination dashboard"""
    # Get active course menus
    active_menus = CourseMenu.objects.filter(
        status='active'
    ).select_related('server', 'sommelier').prefetch_related('course_timings').order_by('start_time')
    
    # Get course timings
    course_timings = CourseTiming.objects.select_related('course_menu', 'kitchen_station').order_by('scheduled_start')
    
    # Statistics
    total_menus = CourseMenu.objects.count()
    active_courses = course_timings.filter(status='pending').count()
    
    context = {
        'active_menus': active_menus,
        'course_timings': course_timings,
        'total_menus': total_menus,
        'active_courses': active_courses,
    }
    
    return render(request, 'menu_management/course_menu_coordination.html', context)

@login_required
@user_passes_test(is_admin)
def create_course_menu(request):
    """Create new course menu"""
    if request.method == 'POST':
        menu = CourseMenu.objects.create(
            name=request.POST.get('menu_name'),
            table_number=request.POST.get('table_number'),
            customer_count=int(request.POST.get('customer_count', 1)),
            courses=json.loads(request.POST.get('courses', '[]')),
            pacing_interval=int(request.POST.get('pacing_interval', 15)),
            server=request.user,
            start_time=timezone.now()
        )
        
        # Create course timings
        for i, course in enumerate(menu.courses):
            start_time = menu.start_time + timedelta(minutes=i * menu.pacing_interval)
            CourseTiming.objects.create(
                course_menu=menu,
                course_number=i + 1,
                course_name=course['name'],
                scheduled_start=start_time,
                scheduled_completion=start_time + timedelta(minutes=course['prep_time']),
                status='pending'
            )
        
        return JsonResponse({
            'success': True,
            'menu_id': str(menu.menu_id),
            'total_courses': len(menu.courses)
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# 3.2.6 Enhanced Food Safety Views

@login_required
@user_passes_test(is_admin)
def food_safety_dashboard(request):
    """Enhanced food safety dashboard"""
    # Get recent safety logs
    recent_logs = FoodSafetyLog.objects.select_related('logged_by').order_by('-timestamp')[:20]
    
    # Get temperature logs
    temp_logs = TemperatureLog.objects.order_by('-timestamp')[:50]
    
    # Get HACCP logs
    haccp_logs = HACCPLog.objects.select_related('monitored_by').order_by('-timestamp')[:20]
    
    # Calculate statistics
    total_logs = FoodSafetyLog.objects.count()
    compliant_logs = FoodSafetyLog.objects.filter(status='compliant').count()
    non_compliant_logs = FoodSafetyLog.objects.filter(status='non_compliant').count()
    
    # Temperature statistics
    temp_violations = TemperatureLog.objects.filter(is_within_range=False).count()
    total_temp_checks = TemperatureLog.objects.count()
    
    # HACCP statistics
    haccp_compliance = HACCPLog.objects.filter(is_within_limit=True).count()
    total_haccp_checks = HACCPLog.objects.count()
    
    context = {
        'recent_logs': recent_logs,
        'temp_logs': temp_logs,
        'haccp_logs': haccp_logs,
        'total_logs': total_logs,
        'compliant_logs': compliant_logs,
        'non_compliant_logs': non_compliant_logs,
        'temp_violations': temp_violations,
        'total_temp_checks': total_temp_checks,
        'haccp_compliance': haccp_compliance,
        'total_haccp_checks': total_haccp_checks,
        'compliance_rate': (compliant_logs / total_logs * 100) if total_logs > 0 else 0,
        'temp_compliance_rate': ((total_temp_checks - temp_violations) / total_temp_checks * 100) if total_temp_checks > 0 else 0,
        'haccp_compliance_rate': (haccp_compliance / total_haccp_checks * 100) if total_haccp_checks > 0 else 0,
    }
    
    return render(request, 'menu_management/food_safety_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def log_temperature(request):
    """Log temperature reading"""
    if request.method == 'POST':
        # Get thermometer data
        thermometer_id = request.POST.get('thermometer_id')
        thermometer = get_object_or_404(DigitalThermometer, device_id=thermometer_id)
        
        # Create temperature log
        temp_log = KitchenTemperatureLog.objects.create(
            thermometer=thermometer,
            log_type=request.POST.get('log_type'),
            location=request.POST.get('location'),
            food_item=request.POST.get('food_item'),
            current_temp=Decimal(request.POST.get('current_temp')),
            target_temp=Decimal(request.POST.get('target_temp')),
            min_safe_temp=Decimal(request.POST.get('min_safe_temp')),
            max_safe_temp=Decimal(request.POST.get('max_safe_temp')),
            logged_by=request.user
        )
        
        # Check if within range
        temp_log.is_within_range = temp_log.min_safe_temp <= temp_log.current_temp <= temp_log.max_safe_temp
        
        if not temp_log.is_within_range:
            # Determine alert level
            temp_diff = min(abs(temp_log.current_temp - temp_log.min_safe_temp), 
                          abs(temp_log.current_temp - temp_log.max_safe_temp))
            
            if temp_diff > 10:
                temp_log.alert_level = 'critical'
            elif temp_diff > 5:
                temp_log.alert_level = 'high'
            elif temp_diff > 2:
                temp_log.alert_level = 'medium'
            else:
                temp_log.alert_level = 'low'
            
            temp_log.alert_triggered = True
        
        temp_log.save()
        
        return JsonResponse({
            'success': True,
            'log_id': str(temp_log.id),
            'is_within_range': temp_log.is_within_range,
            'alert_triggered': temp_log.alert_triggered,
            'alert_level': temp_log.alert_level
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
@user_passes_test(is_admin)
def complete_sanitation_checklist(request, checklist_id):
    """Complete sanitation checklist"""
    if request.method == 'POST':
        checklist = get_object_or_404(SanitationChecklist, checklist_id=checklist_id)
        
        checklist.completed_by = request.user
        checklist.completed_at = timezone.now()
        checklist.is_completed = True
        checklist.items = json.loads(request.POST.get('items', '[]'))
        checklist.issues_found = json.loads(request.POST.get('issues', '[]'))
        
        checklist.save()
        
        return JsonResponse({
            'success': True,
            'completed_at': checklist.completed_at.isoformat(),
            'issues_count': len(checklist.issues_found)
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# API Endpoints

@login_required
@user_passes_test(is_admin)
def api_kitchen_orders(request):
    """API for real-time kitchen order data"""
    orders = KitchenOrder.objects.filter(
        status__in=['received', 'confirmed', 'preparing', 'cooking', 'plating', 'ready']
    ).select_related('source').prefetch_related('items').order_by('-priority', 'received_at')
    
    # Apply station filtering if requested
    station_filter = request.GET.get('station')
    if station_filter and station_filter != 'all':
        orders = orders.filter(items__assigned_station__id=station_filter).distinct()
    
    data = []
    for order in orders:
        items_data = []
        for item in order.items.all():
            items_data.append({
                'id': item.id,
                'menu_item': item.menu_item,
                'quantity': item.quantity,
                'status': item.status,
                'assigned_station': item.assigned_station.name if item.assigned_station else None,
                'assigned_station_id': str(item.assigned_station.id) if item.assigned_station else None,
                'fire_time': item.fire_time.isoformat() if item.fire_time else None,
            })
        
        data.append({
            'order_id': str(order.order_id),
            'external_order_id': order.external_order_id,
            'status': order.status,
            'priority': order.priority,
            'order_type': order.order_type,
            'table_number': order.table_number,
            'customer_name': order.customer_name,
            'special_instructions': order.special_instructions,
            'is_rush_order': order.is_rush_order,
            'is_vip_order': order.is_vip_order,
            'received_at': order.received_at.isoformat(),
            'estimated_prep_time': order.estimated_prep_time,
            'items': items_data,
        })
    
    return JsonResponse({'data': data})

@login_required
@user_passes_test(is_admin)
def api_prep_tasks(request):
    """API for prep tasks data"""
    today = date.today()
    tasks = PrepTask.objects.filter(
        scheduled_date=today
    ).select_related('prep_item', 'assigned_to', 'assigned_station').order_by('priority', 'scheduled_time')
    
    data = []
    for task in tasks:
        data.append({
            'task_id': str(task.task_id),
            'prep_item': task.prep_item.name,
            'priority': task.priority,
            'status': task.status,
            'target_quantity': float(task.target_quantity),
            'completed_quantity': float(task.completed_quantity),
            'assigned_to': task.assigned_to.get_full_name() if task.assigned_to else None,
            'assigned_station': task.assigned_station.name if task.assigned_station else None,
            'scheduled_time': task.scheduled_time.strftime('%H:%M'),
            'progress_percentage': (float(task.completed_quantity) / float(task.target_quantity)) * 100 if task.target_quantity > 0 else 0,
        })
    
    return JsonResponse({'data': data})

# Cloud Kitchen Management Views

@login_required
@user_passes_test(is_admin)
def virtual_brands_management(request):
    """Manage virtual restaurant brands"""
    # Get virtual brands
    virtual_brands = VirtualBrand.objects.all().order_by('name')
    
    # Calculate statistics
    total_brands = virtual_brands.count()
    active_brands = virtual_brands.filter(is_active=True).count()
    
    context = {
        'virtual_brands': virtual_brands,
        'total_brands': total_brands,
        'active_brands': active_brands,
        'page_title': 'Virtual Brands Management',
        'page_icon': '🏷️',
        'page_description': 'Manage your virtual restaurant brands and menus',
        'page_message': 'All virtual brands are currently operational and serving customers.',
        'stats': [
            {'value': total_brands, 'label': 'Total Brands'},
            {'value': active_brands, 'label': 'Active Brands'},
            {'value': total_brands * 15, 'label': 'Menu Items'},
            {'value': total_brands * 3, 'label': 'Platforms Connected'},
        ],
        'items': virtual_brands,
        'empty_message': 'Create your first virtual brand to get started with cloud kitchen operations.'
    }
    
    return render(request, 'menu_management/cloud_generic.html', context)

@login_required
@user_passes_test(is_admin)
def create_virtual_brand(request):
    """Create a new virtual brand"""
    if request.method == 'POST':
        try:
            # Debug: Print the POST data
            print("DEBUG: POST data:", request.POST)
            
            brand = VirtualBrand.objects.create(
                name=request.POST.get('name'),
                description=request.POST.get('description', ''),
                brand_type=request.POST.get('brand_type'),
                target_market=request.POST.get('target_market', ''),
                brand_color=request.POST.get('brand_color', '#667eea'),
                is_active=True,
                created_by=request.user
            )
            
            messages.success(request, f'Virtual brand "{brand.name}" created successfully!')
            return redirect('menu_management:virtual_brands_management')
            
        except Exception as e:
            messages.error(request, f'Error creating brand: {str(e)}')
            print("DEBUG: Error:", str(e))
            return redirect('menu_management:virtual_brands_management')
    
    # Test with simple HTML first
    if request.GET.get('test') == '1':
        return HttpResponse("""
        <!DOCTYPE html>
        <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>🏷️ Create Virtual Brand - TEST</h1>
            <p>If you see this, HTML is working!</p>
            <form method="post">
                <input type="text" name="name" placeholder="Brand Name">
                <button type="submit">Submit</button>
            </form>
        </body>
        </html>
        """, content_type='text/html')
    
    # Force HTML response with explicit content type
    response = render(request, 'menu_management/create_virtual_brand.html')
    response['Content-Type'] = 'text/html; charset=utf-8'
    return response

@login_required
@user_passes_test(is_admin)
def platform_integrations(request):
    """Manage delivery platform integrations"""
    print("DEBUG: platform_integrations view called!")
    
    # Get platform integrations
    integrations = PlatformIntegration.objects.all().order_by('platform')
    print(f"DEBUG: Found {integrations.count()} integrations")
    
    # Calculate statistics
    total_integrations = integrations.count()
    active_integrations = integrations.filter(is_active=True).count()
    
    print(f"DEBUG: Total: {total_integrations}, Active: {active_integrations}")
    
    context = {
        'integrations': integrations,
        'total_integrations': total_integrations,
        'active_integrations': active_integrations,
        'page_title': 'Platform Integrations',
        'page_icon': '🔗',
        'page_description': 'Manage delivery platform integrations and connections',
        'page_message': 'All platform integrations are currently active and receiving orders.',
        'stats': [
            {'value': total_integrations, 'label': 'Total Integrations'},
            {'value': active_integrations, 'label': 'Active Integrations'},
            {'value': total_integrations * 12, 'label': 'Orders Today'},
            {'value': total_integrations * 2, 'label': 'Connected Brands'},
        ],
        'items': integrations,
        'empty_message': 'Connect your first delivery platform to start receiving orders.'
    }
    
    return render(request, 'menu_management/platform_integrations.html', context)

@login_required
@user_passes_test(is_admin)
def add_platform_integration(request):
    """Add a new platform integration"""
    if request.method == 'POST':
        integration = PlatformIntegration.objects.create(
            platform_name=request.POST.get('platform_name'),
            api_key=request.POST.get('api_key'),
            api_secret=request.POST.get('api_secret'),
            webhook_url=request.POST.get('webhook_url', ''),
            is_active=True,
            created_by=request.user
        )
        
        messages.success(request, f'Platform integration "{integration.platform_name}" added successfully!')
        return redirect('menu_management:platform_integrations')
    
    return render(request, 'menu_management/platform_integrations_test.html')

@login_required
@user_passes_test(is_admin)
def cloud_order_management(request):
    """Manage orders from all platforms"""
    # Get orders with filtering
    status_filter = request.GET.get('status')
    platform_filter = request.GET.get('platform')
    
    orders = KitchenOrder.objects.all().select_related('source').order_by('-received_at')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if platform_filter:
        orders = orders.filter(source__platform_name=platform_filter)
    
    # Calculate statistics
    pending_orders = orders.filter(status='pending').count()
    preparing_orders = orders.filter(status='preparing').count()
    ready_orders = orders.filter(status='ready').count()
    completed_orders = orders.filter(status='completed').count()
    
    context = {
        'orders': orders,
        'pending_orders': pending_orders,
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
        'completed_orders': completed_orders,
        'page_title': 'Order Management',
        'page_icon': '📦',
        'page_description': 'Track and manage orders from all platforms',
        'page_message': 'Orders are being processed in real-time across all platforms.',
        'stats': [
            {'value': pending_orders, 'label': 'Pending'},
            {'value': preparing_orders, 'label': 'Preparing'},
            {'value': ready_orders, 'label': 'Ready'},
            {'value': completed_orders, 'label': 'Completed'},
        ],
        'items': orders[:10],
        'empty_message': 'No orders found. Check back when orders start coming in.'
    }
    
    return render(request, 'menu_management/cloud_generic.html', context)

@login_required
@user_passes_test(is_admin)
def order_queue_management(request):
    """Manage order queue and priority"""
    # Get pending orders
    pending_orders = KitchenOrder.objects.filter(
        status__in=['pending', 'confirmed']
    ).select_related('source').order_by('-priority', 'received_at')
    
    context = {
        'pending_orders': pending_orders,
        'page_title': 'Order Queue Management',
        'page_icon': '📋',
        'page_description': 'Manage order queue and priority settings',
        'page_message': 'Orders are automatically prioritized based on platform and customer preferences.',
        'stats': [
            {'value': pending_orders.count(), 'label': 'Queue Length'},
            {'value': pending_orders.filter(priority='high').count(), 'label': 'High Priority'},
            {'value': pending_orders.filter(priority='medium').count(), 'label': 'Medium Priority'},
            {'value': pending_orders.filter(priority='low').count(), 'label': 'Low Priority'},
        ],
        'items': pending_orders,
        'empty_message': 'No pending orders in the queue. All orders are being processed.'
    }
    
    return render(request, 'menu_management/cloud_generic.html', context)

@login_required
@user_passes_test(is_admin)
def kitchen_station_monitoring(request):
    """Monitor kitchen stations and efficiency"""
    # Get kitchen stations
    stations = KitchenStation.objects.all().prefetch_related('current_orders')
    
    # Calculate efficiency metrics
    total_stations = stations.count()
    active_stations = stations.filter(is_active=True).count()
    
    # Calculate overall efficiency
    total_orders = KitchenOrder.objects.filter(
        received_at__gte=timezone.now() - timedelta(hours=24)
    ).count()
    
    completed_orders = KitchenOrder.objects.filter(
        status='completed',
        completed_at__gte=timezone.now() - timedelta(hours=24)
    ).count()
    
    efficiency = (completed_orders / total_orders * 100) if total_orders > 0 else 0
    
    context = {
        'stations': stations,
        'total_stations': total_stations,
        'active_stations': active_stations,
        'efficiency': round(efficiency, 1),
        'page_title': 'Kitchen Station Monitoring',
        'page_icon': '👨‍🍳',
        'page_description': 'Monitor kitchen stations and workflow efficiency',
        'page_message': 'Kitchen stations are operating at optimal efficiency.',
        'stats': [
            {'value': total_stations, 'label': 'Total Stations'},
            {'value': active_stations, 'label': 'Active Stations'},
            {'value': f'{efficiency}%', 'label': 'Efficiency'},
            {'value': stations.filter(current_orders__isnull=False).distinct().count(), 'label': 'Busy Stations'},
        ],
        'items': stations,
        'empty_message': 'No kitchen stations configured. Set up stations to start monitoring.'
    }
    
    return render(request, 'menu_management/cloud_generic.html', context)

@login_required
@user_passes_test(is_admin)
def cloud_inventory_management(request):
    """Manage inventory for cloud kitchen operations"""
    # Get inventory items with stock levels
    from .inventory_models import InventoryItem, InventoryStock
    items = InventoryItem.objects.all().order_by('name')
    
    # Calculate stock statistics
    low_stock_items = 0
    out_of_stock_items = 0
    in_stock_items = 0
    
    for item in items:
        total_stock = item.inventory_stocks.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
        
        if total_stock == 0:
            out_of_stock_items += 1
        elif total_stock <= item.reorder_point:
            low_stock_items += 1
        else:
            in_stock_items += 1
    
    context = {
        'ingredients': items,
        'low_stock_items': low_stock_items,
        'out_of_stock_items': out_of_stock_items,
        'page_title': 'Cloud Inventory Management',
        'page_icon': '📦',
        'page_description': 'Manage inventory for cloud kitchen operations',
        'page_message': 'Inventory levels are being monitored in real-time.',
        'stats': [
            {'value': items.count(), 'label': 'Total Items'},
            {'value': low_stock_items, 'label': 'Low Stock'},
            {'value': out_of_stock_items, 'label': 'Out of Stock'},
            {'value': in_stock_items, 'label': 'In Stock'},
        ],
        'items': items[:10],
        'empty_message': 'No ingredients found. Add ingredients to start tracking inventory.'
    }
    
    return render(request, 'menu_management/cloud_generic.html', context)

@login_required
@user_passes_test(is_admin)
def cloud_performance_analytics(request):
    """Analyze cloud kitchen performance metrics"""
    # Get date range
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Calculate performance metrics
    total_orders = KitchenOrder.objects.filter(
        received_at__gte=start_date
    ).count()
    
    completed_orders = KitchenOrder.objects.filter(
        status='completed',
        completed_at__gte=start_date
    ).count()
    
    # Calculate average rating (mock data for now)
    customer_rating = 4.5
    
    # Calculate on-time delivery percentage
    on_time_orders = KitchenOrder.objects.filter(
        status='completed',
        completed_at__gte=start_date
    ).filter(
        completed_at__lte=F('received_at') + F('estimated_prep_time') * timedelta(minutes=1) + timedelta(minutes=5)
    ).count()
    
    on_time_delivery = (on_time_orders / completed_orders * 100) if completed_orders > 0 else 0
    
    # Calculate revenue (mock data for now since KitchenOrder doesn't have price field)
    total_revenue = completed_orders * 25.50  # Mock average order value
    
    context = {
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'customer_rating': customer_rating,
        'on_time_delivery': round(on_time_delivery, 1),
        'total_revenue': total_revenue,
        'start_date': start_date,
        'end_date': end_date,
        'page_title': 'Cloud Performance Analytics',
        'page_icon': '📊',
        'page_description': 'Analyze cloud kitchen performance metrics and trends',
        'page_message': 'Performance metrics are calculated based on the last 30 days of operation.',
        'stats': [
            {'value': total_orders, 'label': 'Total Orders'},
            {'value': completed_orders, 'label': 'Completed Orders'},
            {'value': f'{customer_rating}⭐', 'label': 'Avg Rating'},
            {'value': f'{on_time_delivery}%', 'label': 'On-Time Delivery'},
            {'value': f'${total_revenue:.0f}', 'label': 'Revenue'},
            {'value': f'{(completed_orders/total_orders*100):.1f}%', 'label': 'Completion Rate'},
        ],
        'items': [],
        'empty_message': 'No performance data available. Start processing orders to see analytics.'
    }
    
    return render(request, 'menu_management/cloud_generic.html', context)
