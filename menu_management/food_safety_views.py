from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Avg
from .models import FoodSafetyLog, TemperatureLog, HACCPLog
import json

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
@user_passes_test(is_admin)
def food_safety_dashboard(request):
    """Food safety management dashboard"""
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
def create_safety_log(request):
    """Create a new food safety log"""
    if request.method == 'POST':
        log = FoodSafetyLog.objects.create(
            log_type=request.POST['log_type'],
            priority=request.POST['priority'],
            location=request.POST['location'],
            station=request.POST.get('station', ''),
            temperature=float(request.POST.get('temperature', 0)) if request.POST.get('temperature') else None,
            target_temperature=float(request.POST.get('target_temperature', 0)) if request.POST.get('target_temperature') else None,
            description=request.POST['description'],
            notes=request.POST.get('notes', ''),
            logged_by=request.user,
            is_automated=False
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Safety log created successfully',
            'log_id': log.id
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_admin)
def create_temperature_log(request):
    """Create a new temperature log"""
    if request.method == 'POST':
        log = TemperatureLog.objects.create(
            sensor_type=request.POST['sensor_type'],
            sensor_id=request.POST['sensor_id'],
            location=request.POST['location'],
            current_temp=float(request.POST['current_temp']),
            target_temp=float(request.POST['target_temp']),
            min_safe_temp=float(request.POST['min_safe_temp']),
            max_safe_temp=float(request.POST['max_safe_temp']),
            food_item=request.POST.get('food_item', ''),
            measurement_context=request.POST.get('measurement_context', ''),
        )
        
        # Check temperature range
        log.check_temperature_range()
        
        return JsonResponse({
            'success': True,
            'message': f'Temperature log created successfully',
            'log_id': log.id,
            'is_within_range': log.is_within_range,
            'alert_triggered': log.alert_triggered
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_admin)
def create_haccp_log(request):
    """Create a new HACCP log"""
    if request.method == 'POST':
        log = HACCPLog.objects.create(
            ccp=request.POST['ccp'],
            location=request.POST['location'],
            critical_limit=request.POST['critical_limit'],
            actual_value=request.POST['actual_value'],
            is_within_limit=request.POST.get('is_within_limit', 'False') == 'True',
            monitored_by=request.user,
            notes=request.POST.get('notes', ''),
        )
        
        return JsonResponse({
            'success': True,
            'message': f'HACCP log created successfully',
            'log_id': log.id
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_admin)
def get_safety_statistics(request):
    """Get food safety statistics for dashboard"""
    # Recent compliance rates
    today = timezone.now().date()
    today_logs = FoodSafetyLog.objects.filter(timestamp__date=today)
    
    today_compliance = today_logs.filter(status='compliant').count()
    today_total = today_logs.count()
    
    # Temperature violations today
    today_temp_violations = TemperatureLog.objects.filter(
        timestamp__date=today,
        is_within_range=False
    ).count()
    
    # HACCP compliance today
    today_haccp = HACCPLog.objects.filter(timestamp__date=today)
    today_haccp_compliant = today_haccp.filter(is_within_limit=True).count()
    
    return JsonResponse({
        'today_compliance_rate': (today_compliance / today_total * 100) if today_total > 0 else 0,
        'today_temp_violations': today_temp_violations,
        'today_haccp_compliance_rate': (today_haccp_compliant / today_haccp.count() * 100) if today_haccp.count() > 0 else 0,
        'total_logs_today': today_total,
    })
