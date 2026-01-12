from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count, Avg, Q, F, Expression, FloatField
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta, date
from decimal import Decimal
import json

from .models import *
from .inventory_models import *
from .staff_models import *

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

# INVENTORY MANAGEMENT VIEWS

@login_required
@user_passes_test(is_admin)
def inventory_dashboard(request):
    """Main inventory management dashboard"""
    # Get inventory statistics
    total_items = InventoryItem.objects.filter(is_active=True).count()
    low_stock_items = InventoryItem.objects.filter(
        inventory_stocks__available_quantity__lte=F('reorder_point')
    ).distinct().count()
    
    expiring_soon = InventoryBatch.objects.filter(
        expiration_date__lte=timezone.now().date() + timezone.timedelta(days=7),
        is_active=True
    ).count()
    
    # Get recent transactions
    recent_transactions = InventoryTransaction.objects.select_related(
        'item', 'location', 'created_by'
    ).order_by('-created_at')[:10]
    
    # Get critical alerts
    critical_alerts = []
    
    # Low stock alerts
    for item in InventoryItem.objects.filter(is_active=True):
        total_stock = item.inventory_stocks.aggregate(
            total=Sum('available_quantity')
        )['total'] or 0
        if total_stock <= item.reorder_point:
            critical_alerts.append({
                'type': 'low_stock',
                'item': item.name,
                'current': total_stock,
                'required': item.reorder_point,
                'priority': 'high' if total_stock <= item.reorder_point * Decimal('0.5') else 'medium'
            })
    
    # Expiration alerts
    expiring_batches = InventoryBatch.objects.filter(
        expiration_date__lte=timezone.now().date() + timezone.timedelta(days=7),
        is_active=True,
        quantity__gt=0
    ).select_related('item', 'location')
    
    for batch in expiring_batches:
        critical_alerts.append({
            'type': 'expiring',
            'item': batch.item.name,
            'batch': batch.batch_number,
            'location': batch.location.name,
            'days_left': batch.days_until_expiration,
            'priority': 'critical' if batch.days_until_expiration < 0 else 'high'
        })
    
    context = {
        'total_items': total_items,
        'low_stock_items': low_stock_items,
        'expiring_soon': expiring_soon,
        'recent_transactions': recent_transactions,
        'critical_alerts': critical_alerts[:10],  # Show top 10 alerts
    }
    
    return render(request, 'menu_management/inventory_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def inventory_items_list(request):
    """List all inventory items with search and filtering"""
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    location = request.GET.get('location', '')
    
    items = InventoryItem.objects.filter(is_active=True).prefetch_related(
        'inventory_stocks__location'
    ).prefetch_related('batches')
    
    if search:
        items = items.filter(
            Q(name__icontains=search) | 
            Q(sku__icontains=search) | 
            Q(description__icontains=search)
        )
    
    if category:
        items = items.filter(category=category)
    
    if location:
        items = items.filter(inventory_stocks__location_id=location)
    
    # Add stock information
    items_data = []
    for item in items:
        total_stock = item.inventory_stocks.aggregate(
            total=Sum('available_quantity')
        )['total'] or 0
        total_value = item.inventory_stocks.aggregate(
            total=Sum(F('available_quantity') * item.current_cost, output_field=FloatField())
        )['total'] or 0
        
        items_data.append({
            'item': item,
            'total_stock': total_stock,
            'total_value': total_value,
            'is_low_stock': total_stock <= item.reorder_point,
            'is_critical_stock': total_stock <= item.reorder_point * Decimal('0.5'),
            'locations': item.inventory_stocks.all()
        })
    
    paginator = Paginator(items_data, 20)
    page = request.GET.get('page')
    items_page = paginator.get_page(page)
    
    # Get filter options
    categories = InventoryItem.objects.values_list('category', flat=True).distinct()
    locations = StorageLocation.objects.filter(is_active=True)
    
    context = {
        'items': items_page,
        'categories': categories,
        'locations': locations,
        'search': search,
        'selected_category': category,
        'selected_location': location,
    }
    
    return render(request, 'menu_management/inventory_items.html', context)

@login_required
@user_passes_test(is_admin)
def create_inventory_item(request):
    """Create a new inventory item for reordering"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        sku = request.POST.get('sku', '')
        barcode = request.POST.get('barcode', '')
        unit = request.POST.get('unit')
        category = request.POST.get('category')
        is_perishable = request.POST.get('is_perishable') == 'on'
        shelf_life_days = request.POST.get('shelf_life_days')
        storage_requirements = request.POST.get('storage_requirements', '')
        standard_cost = request.POST.get('standard_cost', 0)
        current_cost = request.POST.get('current_cost', 0)
        par_level = request.POST.get('par_level', 0)
        reorder_point = request.POST.get('reorder_point', 0)
        max_level = request.POST.get('max_level', 0)
        
        # Validation
        if not all([name, unit, category]):
            messages.error(request, 'Name, unit, and category are required fields.')
            return render(request, 'menu_management/create_inventory_item.html', {
                'form_data': request.POST,
                'unit_choices': InventoryItem.UNIT_CHOICES,
                'categories': InventoryItem.objects.values_list('category', flat=True).distinct()
            })
        
        try:
            # Generate unique SKU if not provided
            if not sku:
                sku = f"INV-{name.upper().replace(' ', '-')[:10]}-{timezone.now().strftime('%Y%m%d')}"
            
            inventory_item = InventoryItem.objects.create(
                name=name,
                description=description,
                sku=sku,
                barcode=barcode,
                unit=unit,
                category=category,
                is_perishable=is_perishable,
                shelf_life_days=int(shelf_life_days) if shelf_life_days else None,
                storage_requirements=storage_requirements,
                standard_cost=Decimal(standard_cost),
                current_cost=Decimal(current_cost),
                par_level=Decimal(par_level),
                reorder_point=Decimal(reorder_point),
                max_level=Decimal(max_level),
                is_active=True
            )
            
            messages.success(request, f'Inventory item "{name}" created successfully! SKU: {sku}')
            return redirect('menu_management:inventory_items')
            
        except IntegrityError as e:
            messages.error(request, f'Error creating inventory item: {str(e)}')
            return render(request, 'menu_management/create_inventory_item.html', {
                'form_data': request.POST,
                'unit_choices': InventoryItem.UNIT_CHOICES,
                'categories': InventoryItem.objects.values_list('category', flat=True).distinct()
            })
        except Exception as e:
            messages.error(request, f'Error creating inventory item: {str(e)}')
            return render(request, 'menu_management/create_inventory_item.html', {
                'form_data': request.POST,
                'unit_choices': InventoryItem.UNIT_CHOICES,
                'categories': InventoryItem.objects.values_list('category', flat=True).distinct()
            })
    
    return render(request, 'menu_management/create_inventory_item.html', {
        'form_data': {},
        'unit_choices': InventoryItem.UNIT_CHOICES,
        'categories': InventoryItem.objects.values_list('category', flat=True).distinct()
    })

@login_required
@user_passes_test(is_admin)
def inventory_transactions(request):
    """View and manage inventory transactions"""
    transaction_type = request.GET.get('type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    transactions = InventoryTransaction.objects.select_related(
        'item', 'location', 'created_by', 'batch'
    ).order_by('-created_at')
    
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    if date_from:
        transactions = transactions.filter(created_at__date__gte=date_from)
    
    if date_to:
        transactions = transactions.filter(created_at__date__lte=date_to)
    
    paginator = Paginator(transactions, 50)
    page = request.GET.get('page')
    transactions_page = paginator.get_page(page)
    
    context = {
        'transactions': transactions_page,
        'transaction_types': InventoryTransaction.TRANSACTION_TYPES,
        'selected_type': transaction_type,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'menu_management/inventory_transactions.html', context)

@login_required
@user_passes_test(is_admin)
def purchase_orders(request):
    """Manage purchase orders"""
    status = request.GET.get('status', '')
    
    orders = PurchaseOrder.objects.select_related('vendor', 'created_by', 'approved_by').prefetch_related('items').order_by('-order_date')
    
    if status:
        orders = orders.filter(status=status)
    
    paginator = Paginator(orders, 20)
    page = request.GET.get('page')
    orders_page = paginator.get_page(page)
    
    context = {
        'orders': orders_page,
        'status_choices': PurchaseOrder.STATUS_CHOICES,
        'selected_status': status,
    }
    
    return render(request, 'menu_management/purchase_orders.html', context)

@login_required
@user_passes_test(is_admin)
def waste_tracking(request):
    """Track waste and spoilage"""
    waste_type = request.GET.get('type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    waste_records = WasteRecord.objects.select_related(
        'item', 'location', 'reported_by', 'batch'
    ).order_by('-reported_at')
    
    if waste_type:
        waste_records = waste_records.filter(waste_type=waste_type)
    
    if date_from:
        waste_records = waste_records.filter(reported_at__date__gte=date_from)
    
    if date_to:
        waste_records = waste_records.filter(reported_at__date__lte=date_to)
    
    # Calculate waste statistics
    total_waste_cost = waste_records.aggregate(
        total=Sum('estimated_cost')
    )['total'] or 0
    
    waste_by_type = waste_records.values('waste_type').annotate(
        count=Count('id'),
        total_cost=Sum('estimated_cost')
    ).order_by('-total_cost')
    
    paginator = Paginator(waste_records, 50)
    page = request.GET.get('page')
    waste_page = paginator.get_page(page)
    
    context = {
        'waste_records': waste_page,
        'waste_types': WasteRecord.WASTE_TYPES,
        'selected_type': waste_type,
        'date_from': date_from,
        'date_to': date_to,
        'total_waste_cost': total_waste_cost,
        'waste_by_type': waste_by_type,
    }
    
    return render(request, 'menu_management/waste_tracking.html', context)

@login_required
@user_passes_test(is_admin)
def inventory_reports(request):
    """Inventory analytics and reports"""
    # Cost analysis
    total_inventory_value = InventoryStock.objects.aggregate(
        total=Sum(F('available_quantity') * F('item__current_cost'), output_field=FloatField())
    )['total'] or 0
    
    # Top items by value
    top_items = InventoryItem.objects.filter(is_active=True).annotate(
        total_stock=Sum('inventory_stocks__available_quantity'),
        total_value=Sum(F('inventory_stocks__available_quantity') * F('current_cost'), output_field=FloatField())
    ).order_by('-total_value')[:10]
    
    # Category breakdown
    category_breakdown = InventoryItem.objects.filter(is_active=True).values('category').annotate(
        item_count=Count('id'),
        total_value=Sum(F('inventory_stocks__available_quantity') * F('current_cost'), output_field=FloatField())
    ).order_by('-total_value')
    
    # Location utilization
    location_stats = StorageLocation.objects.filter(is_active=True).annotate(
        item_count=Count('inventory_stocks'),
        total_value=Sum(F('inventory_stocks__available_quantity') * F('inventory_stocks__item__current_cost'), output_field=FloatField())
    ).order_by('-total_value')
    
    # Recent waste trends
    waste_trend = WasteRecord.objects.filter(
        reported_at__gte=timezone.now() - timezone.timedelta(days=30)
    ).values('reported_at__date').annotate(
        daily_cost=Sum('estimated_cost'),
        daily_count=Count('id')
    ).order_by('reported_at__date')
    
    context = {
        'total_inventory_value': total_inventory_value,
        'top_items': top_items,
        'category_breakdown': category_breakdown,
        'location_stats': location_stats,
        'waste_trend': waste_trend,
    }
    
    return render(request, 'menu_management/inventory_reports.html', context)

# STAFF MANAGEMENT VIEWS

@login_required
@user_passes_test(is_admin)
def staff_dashboard(request):
    """Main staff management dashboard"""
    # Staff statistics
    total_staff = StaffProfile.objects.filter(is_active=True).count()
    on_duty_staff = Schedule.objects.filter(
        date=timezone.now().date(),
        status='active'
    ).count()
    
    # Pending requests
    pending_swaps = ShiftSwap.objects.filter(status='requested').count()
    pending_timeoff = TimeOffRequest.objects.filter(status='requested').count()
    
    # Today's schedule
    today_schedule = Schedule.objects.filter(
        date=timezone.now().date()
    ).select_related('staff', 'staff__user').order_by('start_time')
    
    # Overdue tasks
    overdue_tasks = Task.objects.filter(
        due_date__lt=timezone.now(),
        status__in=['pending', 'in_progress']
    ).count()
    
    context = {
        'total_staff': total_staff,
        'on_duty_staff': on_duty_staff,
        'pending_swaps': pending_swaps,
        'pending_timeoff': pending_timeoff,
        'today_schedule': today_schedule,
        'overdue_tasks': overdue_tasks,
    }
    
    return render(request, 'menu_management/staff_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def staff_scheduling(request):
    """Staff scheduling interface"""
    view_date = request.GET.get('date', timezone.now().date())
    view_type = request.GET.get('view', 'day')  # day, week, month
    
    schedules = Schedule.objects.filter(
        date=view_date
    ).select_related('staff', 'staff__user', 'shift_template').order_by('start_time')
    
    # Get all active staff for scheduling
    active_staff = StaffProfile.objects.filter(is_active=True).select_related('user')
    
    # Get shift templates
    shift_templates = ShiftTemplate.objects.filter(is_active=True)
    
    context = {
        'view_date': view_date,
        'view_type': view_type,
        'schedules': schedules,
        'active_staff': active_staff,
        'shift_templates': shift_templates,
    }
    
    return render(request, 'menu_management/staff_scheduling.html', context)

@login_required
@user_passes_test(is_admin)
def create_schedule(request):
    """Create new schedule"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            staff_id = data.get('staff_id')
            date = data.get('date')
            start_time = data.get('start_time')
            end_time = data.get('end_time')
            
            if not all([staff_id, date, start_time, end_time]):
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required fields'
                })
            
            # Parse date and times
            schedule_date = timezone.datetime.strptime(date, '%Y-%m-%d').date()
            start_time_obj = timezone.datetime.strptime(start_time, '%H:%M').time()
            end_time_obj = timezone.datetime.strptime(end_time, '%H:%M').time()
            
            # Get staff profile
            staff = get_object_or_404(StaffProfile, id=staff_id)
            
            # Check for conflicts
            existing_schedule = Schedule.objects.filter(
                staff=staff,
                date=schedule_date,
                start_time=start_time_obj
            ).first()
            
            if existing_schedule:
                return JsonResponse({
                    'success': False,
                    'error': 'Staff member already scheduled at this time'
                })
            
            # Create schedule
            schedule = Schedule.objects.create(
                staff=staff,
                date=schedule_date,
                start_time=start_time_obj,
                end_time=end_time_obj,
                shift_template_id=data.get('shift_template_id'),
                break_duration=data.get('break_duration', 30),
                station=data.get('station', ''),
                role=data.get('role', ''),
                status=data.get('status', 'draft'),
                notes=data.get('notes', ''),
                is_overtime=data.get('is_overtime', False),
                created_by=request.user
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Schedule created successfully',
                'schedule': {
                    'id': str(schedule.schedule_id),
                    'staff_name': schedule.staff.user.get_full_name(),
                    'date': schedule.date.strftime('%Y-%m-%d'),
                    'start_time': schedule.start_time.strftime('%H:%M'),
                    'end_time': schedule.end_time.strftime('%H:%M'),
                    'status': schedule.status
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

@login_required
@user_passes_test(is_admin)
def get_schedule_data(request, schedule_id):
    """Get schedule data for editing"""
    if request.method == 'GET':
        try:
            schedule = get_object_or_404(Schedule, schedule_id=schedule_id)
            
            # Get staff name with fallback
            staff_name = schedule.staff.user.get_full_name()
            if not staff_name:
                staff_name = schedule.staff.user.username
            
            return JsonResponse({
                'success': True,
                'schedule': {
                    'id': str(schedule.schedule_id),
                    'staff_id': schedule.staff.id,
                    'staff_name': staff_name,
                    'date': schedule.date.strftime('%Y-%m-%d'),
                    'start_time': schedule.start_time.strftime('%H:%M'),
                    'end_time': schedule.end_time.strftime('%H:%M'),
                    'shift_template_id': schedule.shift_template.id if schedule.shift_template else None,
                    'break_duration': schedule.break_duration,
                    'station': schedule.station,
                    'role': schedule.role,
                    'status': schedule.status,
                    'notes': schedule.notes,
                    'is_overtime': schedule.is_overtime
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

@login_required
@user_passes_test(is_admin)
def update_schedule(request, schedule_id):
    """Update existing schedule"""
    if request.method == 'PUT':
        try:
            schedule = get_object_or_404(Schedule, schedule_id=schedule_id)
            data = json.loads(request.body)
            
            # Update fields
            if 'staff_id' in data:
                schedule.staff_id = data['staff_id']
            if 'date' in data:
                schedule.date = timezone.datetime.strptime(data['date'], '%Y-%m-%d').date()
            if 'start_time' in data:
                schedule.start_time = timezone.datetime.strptime(data['start_time'], '%H:%M').time()
            if 'end_time' in data:
                schedule.end_time = timezone.datetime.strptime(data['end_time'], '%H:%M').time()
            if 'shift_template_id' in data:
                schedule.shift_template_id = data['shift_template_id']
            if 'break_duration' in data:
                schedule.break_duration = data['break_duration']
            if 'station' in data:
                schedule.station = data['station']
            if 'role' in data:
                schedule.role = data['role']
            if 'status' in data:
                schedule.status = data['status']
            if 'notes' in data:
                schedule.notes = data['notes']
            if 'is_overtime' in data:
                schedule.is_overtime = data['is_overtime']
            
            schedule.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Schedule updated successfully',
                'schedule': {
                    'id': str(schedule.schedule_id),
                    'staff_name': schedule.staff.user.get_full_name(),
                    'date': schedule.date.strftime('%Y-%m-%d'),
                    'start_time': schedule.start_time.strftime('%H:%M'),
                    'end_time': schedule.end_time.strftime('%H:%M'),
                    'status': schedule.status
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

@login_required
@user_passes_test(is_admin)
def delete_schedule(request, schedule_id):
    """Delete schedule"""
    if request.method == 'DELETE':
        try:
            schedule = get_object_or_404(Schedule, schedule_id=schedule_id)
            schedule.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Schedule deleted successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

@login_required
@user_passes_test(is_admin)
def get_shift_template_details(request, template_id):
    """Get shift template details"""
    if request.method == 'GET':
        try:
            template = get_object_or_404(ShiftTemplate, id=template_id)
            
            return JsonResponse({
                'success': True,
                'template': {
                    'id': template.id,
                    'name': template.name,
                    'start_time': template.start_time.strftime('%H:%M'),
                    'end_time': template.end_time.strftime('%H:%M'),
                    'break_duration': template.break_duration,
                    'description': template.description
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

@login_required
@user_passes_test(is_admin)
def task_management(request):
    """Task management system"""
    status = request.GET.get('status', '')
    assigned_to = request.GET.get('assigned_to', '')
    priority = request.GET.get('priority', '')
    
    tasks = Task.objects.select_related(
        'assigned_to', 'assigned_to__user', 'assigned_by'
    ).order_by('-created_at')
    
    if status:
        tasks = tasks.filter(status=status)
    
    if assigned_to:
        tasks = tasks.filter(assigned_to_id=assigned_to)
    
    if priority:
        tasks = tasks.filter(priority=priority)
    
    paginator = Paginator(tasks, 20)
    page = request.GET.get('page')
    tasks_page = paginator.get_page(page)
    
    # Get filter options
    active_staff = StaffProfile.objects.filter(is_active=True)
    
    # DEBUG: Print debug information
    print(f"DEBUG: tasks_page count: {len(tasks_page)}")
    print(f"DEBUG: tasks_page type: {type(tasks_page)}")
    for i, task in enumerate(tasks_page):
        print(f"DEBUG: Task {i+1}: {task.title}")
    
    context = {
        'tasks_page': tasks_page,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
        'task_types': Task.TASK_TYPES,
        'selected_status': status,
        'selected_assigned_to': assigned_to,
        'selected_priority': priority,
        'active_staff': active_staff,
    }
    
    return render(request, 'menu_management/task_management.html', context)

@login_required
@user_passes_test(is_admin)
def staff_communications(request):
    """Internal communications system"""
    message_type = request.GET.get('type', '')
    
    messages = Communication.objects.select_related(
        'sender'
    ).prefetch_related('recipients').order_by('-created_at')
    
    if message_type:
        messages = messages.filter(message_type=message_type)
    
    paginator = Paginator(messages, 20)
    page = request.GET.get('page')
    messages_page = paginator.get_page(page)
    
    context = {
        'messages': messages_page,
        'message_types': Communication.MESSAGE_TYPES,
        'selected_type': message_type,
    }
    
    return render(request, 'menu_management/staff_communications.html', context)

@login_required
@user_passes_test(is_admin)
def staff_reports(request):
    """Staff analytics and reports"""
    # Labor cost analysis
    labor_costs = Schedule.objects.filter(
        date__gte=timezone.now() - timezone.timedelta(days=30)
    ).aggregate(
        total_cost=Sum(F('duration_hours') * F('staff__hourly_rate'), output_field=FloatField()),
        total_hours=Sum('duration_hours')
    )
    
    # Staff performance
    staff_performance = StaffProfile.objects.filter(is_active=True).annotate(
        scheduled_hours=Sum('schedules__duration_hours', filter=Q(schedules__date__gte=timezone.now() - timezone.timedelta(days=30))),
        completed_tasks=Count('assigned_tasks', filter=Q(assigned_tasks__status='completed'))
    ).order_by('-scheduled_hours')
    
    # Task completion trends
    task_trends = Task.objects.filter(
        created_at__gte=timezone.now() - timezone.timedelta(days=30)
    ).values('created_at__date').annotate(
        created=Count('id'),
        completed=Count('id', filter=Q(status='completed'))
    ).order_by('created_at__date')
    
    context = {
        'labor_costs': labor_costs,
        'staff_performance': staff_performance,
        'task_trends': task_trends,
    }
    
    return render(request, 'menu_management/staff_reports.html', context)

# API ENDPOINTS

@login_required
@user_passes_test(is_admin)
def api_inventory_levels(request):
    """Get current inventory levels for dashboard"""
    items = InventoryItem.objects.filter(is_active=True).annotate(
        total_stock=Sum('inventory_stocks__available_quantity'),
        total_value=Sum(F('inventory_stocks__available_quantity') * F('current_cost'), output_field=FloatField())
    ).order_by('-total_value')
    
    data = []
    for item in items:
        data.append({
            'name': item.name,
            'category': item.category,
            'current_stock': float(item.total_stock or 0),
            'reorder_point': float(item.reorder_point),
            'unit_cost': float(item.current_cost),
            'total_value': float(item.total_value or 0),
            'is_low_stock': (item.total_stock or 0) <= item.reorder_point,
        })
    
    return JsonResponse({'data': data})

@login_required
@user_passes_test(is_admin)
def api_staff_schedule(request):
    """Get staff schedule for calendar view"""
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    schedules = Schedule.objects.filter(
        date__gte=date_from,
        date__lte=date_to
    ).select_related('staff', 'staff__user')
    
    data = []
    for schedule in schedules:
        data.append({
            'id': str(schedule.schedule_id),
            'title': f"{schedule.staff.user.get_full_name()} - {schedule.role or 'Staff'}",
            'start': f"{schedule.date}T{schedule.start_time}",
            'end': f"{schedule.date}T{schedule.end_time}",
            'color': '#007bff' if schedule.status == 'active' else '#6c757d',
            'extendedProps': {
                'staff_id': schedule.staff.id,
                'role': schedule.role,
                'station': schedule.station,
                'status': schedule.status,
            }
        })
    
    return JsonResponse({'data': data})
