from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from decimal import Decimal
import json
from datetime import timedelta, date, time

from .enhanced_course_menu_models import (
    CourseMenuTemplate, CourseMenuInstance, CourseDefinition, 
    CourseInstance, WinePairing, BeveragePairing, CourseMenuPricing
)
from .kitchen_operations_models import KitchenStation

def is_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_admin)
def enhanced_course_menu_dashboard(request):
    """Enhanced course menu management dashboard"""
    # Get statistics
    total_templates = CourseMenuTemplate.objects.filter(is_active=True).count()
    active_instances = CourseMenuInstance.objects.filter(status='in_progress').count()
    total_instances = CourseMenuInstance.objects.count()
    
    # Recent instances
    recent_instances = CourseMenuInstance.objects.select_related(
        'template', 'server', 'sommelier'
    ).order_by('-created_at')[:10]
    
    # Menu types breakdown
    menu_types = CourseMenuTemplate.objects.filter(is_active=True).values(
        'menu_type'
    ).annotate(count=Count('template_id'))
    
    # Dietary accommodations stats
    dietary_stats = {
        'vegetarian': CourseMenuTemplate.objects.filter(is_active=True, vegetarian_available=True).count(),
        'vegan': CourseMenuTemplate.objects.filter(is_active=True, vegan_available=True).count(),
        'gluten_free': CourseMenuTemplate.objects.filter(is_active=True, gluten_free_available=True).count(),
    }
    
    context = {
        'total_templates': total_templates,
        'active_instances': active_instances,
        'total_instances': total_instances,
        'recent_instances': recent_instances,
        'menu_types': menu_types,
        'dietary_stats': dietary_stats,
    }
    
    return render(request, 'menu_management/enhanced_course_menu_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def course_menu_templates(request):
    """Manage course menu templates"""
    templates = CourseMenuTemplate.objects.filter(is_active=True).order_by('name')
    
    # Filter by menu type
    menu_type = request.GET.get('menu_type')
    if menu_type:
        templates = templates.filter(menu_type=menu_type)
    
    # Filter by dietary options
    dietary = request.GET.get('dietary')
    if dietary == 'vegetarian':
        templates = templates.filter(vegetarian_available=True)
    elif dietary == 'vegan':
        templates = templates.filter(vegan_available=True)
    elif dietary == 'gluten_free':
        templates = templates.filter(gluten_free_available=True)
    
    paginator = Paginator(templates, 12)
    page = request.GET.get('page')
    templates_page = paginator.get_page(page)
    
    context = {
        'templates': templates_page,
        'menu_types': CourseMenuTemplate.MENU_TYPE_CHOICES,
        'current_filters': {
            'menu_type': menu_type,
            'dietary': dietary,
        }
    }
    
    return render(request, 'menu_management/course_menu_templates.html', context)

@login_required
@user_passes_test(is_admin)
def create_course_menu_template(request):
    """Create new course menu template"""
    if request.method == 'POST':
        template = CourseMenuTemplate.objects.create(
            name=request.POST.get('name'),
            description=request.POST.get('description'),
            course_count=int(request.POST.get('course_count')),
            menu_type=request.POST.get('menu_type'),
            base_price=Decimal(request.POST.get('base_price')),
            price_per_person=Decimal(request.POST.get('price_per_person')),
            min_party_size=int(request.POST.get('min_party_size', 1)),
            max_party_size=int(request.POST.get('max_party_size', 10)),
            advance_booking_days=int(request.POST.get('advance_booking_days', 1)),
            vegetarian_available='vegetarian_available' in request.POST,
            vegan_available='vegan_available' in request.POST,
            gluten_free_available='gluten_free_available' in request.POST,
            wine_pairing_available='wine_pairing_available' in request.POST,
            beverage_pairing_available='beverage_pairing_available' in request.POST,
            sommelier_required='sommelier_required' in request.POST,
            is_seasonal='is_seasonal' in request.POST,
            holiday_specific='holiday_specific' in request.POST,
            holiday_name=request.POST.get('holiday_name', ''),
            chef_table_exclusive='chef_table_exclusive' in request.POST,
            required_chef_level=request.POST.get('required_chef_level', 'line_cook'),
            chef_notes=request.POST.get('chef_notes', ''),
            estimated_duration=int(request.POST.get('estimated_duration', 120)),
            pacing_interval=int(request.POST.get('pacing_interval', 15)),
        )
        
        # Handle seasonal months
        if template.is_seasonal:
            season_months = request.POST.getlist('season_months')
            template.season_months = [int(month) for month in season_months]
        
        # Handle dietary options
        dietary_options = request.POST.getlist('dietary_options')
        template.other_dietary_options = dietary_options
        
        # Handle price tiers
        price_tiers = {}
        tier_names = request.POST.getlist('tier_name')
        tier_prices = request.POST.getlist('tier_price')
        tier_min_sizes = request.POST.getlist('tier_min_size')
        tier_max_sizes = request.POST.getlist('tier_max_size')
        
        for i, name in enumerate(tier_names):
            if name and i < len(tier_prices):
                price_tiers[name] = {
                    'price': float(tier_prices[i]),
                    'min_size': int(tier_min_sizes[i]) if i < len(tier_min_sizes) else 1,
                    'max_size': int(tier_max_sizes[i]) if i < len(tier_max_sizes) else 10,
                }
        
        template.price_tiers = price_tiers
        
        return redirect('menu_management:course_menu_template_detail', template_id=template.template_id)
    
    return render(request, 'menu_management/create_course_menu_template.html')

@login_required
@user_passes_test(is_admin)
def course_menu_template_detail(request, template_id):
    """Course menu template detail and course management"""
    template = get_object_or_404(CourseMenuTemplate, template_id=template_id)
    
    # Get courses for this template
    courses = CourseDefinition.objects.filter(template=template).order_by('order', 'course_number')
    
    # Get pricing tiers
    pricing_tiers = CourseMenuPricing.objects.filter(template=template, is_active=True)
    
    # Get wine pairings
    wine_pairings = WinePairing.objects.filter(course_definition__template=template)
    
    # Get beverage pairings
    beverage_pairings = BeveragePairing.objects.filter(course_definition__template=template)
    
    context = {
        'template': template,
        'courses': courses,
        'pricing_tiers': pricing_tiers,
        'wine_pairings': wine_pairings,
        'beverage_pairings': beverage_pairings,
    }
    
    return render(request, 'menu_management/course_menu_template_detail.html', context)

@login_required
@user_passes_test(is_admin)
def edit_course_menu_template(request, template_id):
    """Edit a course menu template"""
    template = get_object_or_404(CourseMenuTemplate, template_id=template_id)
    
    if request.method == 'POST':
        # Update template fields
        template.name = request.POST.get('name')
        template.description = request.POST.get('description')
        template.course_count = int(request.POST.get('course_count'))
        template.menu_type = request.POST.get('menu_type')
        template.base_price = Decimal(request.POST.get('base_price'))
        template.price_per_person = Decimal(request.POST.get('price_per_person'))
        template.min_party_size = int(request.POST.get('min_party_size'))
        template.max_party_size = int(request.POST.get('max_party_size'))
        template.advance_booking_days = int(request.POST.get('advance_booking_days'))
        
        # Dietary options
        template.vegetarian_available = request.POST.get('vegetarian_available') == 'on'
        template.vegan_available = request.POST.get('vegan_available') == 'on'
        template.gluten_free_available = request.POST.get('gluten_free_available') == 'on'
        
        # Pairing options
        template.wine_pairing_available = request.POST.get('wine_pairing_available') == 'on'
        template.beverage_pairing_available = request.POST.get('beverage_pairing_available') == 'on'
        template.sommelier_required = request.POST.get('sommelier_required') == 'on'
        
        # Seasonal and holiday options
        template.is_seasonal = request.POST.get('is_seasonal') == 'on'
        template.holiday_specific = request.POST.get('holiday_specific') == 'on'
        
        if template.is_seasonal:
            season_months = request.POST.getlist('season_months')
            template.season_months = season_months
        
        if template.holiday_specific:
            template.holiday_name = request.POST.get('holiday_name')
        
        template.save()
        
        return redirect('menu_management:course_menu_template_detail', template_id=template.template_id)
    
    return render(request, 'menu_management/edit_course_menu_template.html', {'template': template})

@login_required
@user_passes_test(is_admin)
def add_course_to_template(request, template_id):
    """Add a course to a menu template"""
    template = get_object_or_404(CourseMenuTemplate, template_id=template_id)
    
    if request.method == 'POST':
        course = CourseDefinition.objects.create(
            template=template,
            course_number=int(request.POST.get('course_number')),
            course_name=request.POST.get('course_name'),
            description=request.POST.get('description'),
            chef_notes=request.POST.get('chef_notes', ''),
            prep_time=int(request.POST.get('prep_time', 20)),
            plating_time=int(request.POST.get('plating_time', 5)),
            presentation_time=int(request.POST.get('presentation_time', 2)),
            main_ingredients=json.loads(request.POST.get('main_ingredients', '[]')),
            complexity_level=request.POST.get('complexity_level'),
            is_vegetarian='is_vegetarian' in request.POST,
            is_vegan='is_vegan' in request.POST,
            is_gluten_free='is_gluten_free' in request.POST,
            contains_nuts='contains_nuts' in request.POST,
            contains_dairy='contains_dairy' in request.POST,
            allergens=json.loads(request.POST.get('allergens', '[]')),
            wine_pairing_notes=request.POST.get('wine_pairing_notes', ''),
            beverage_pairing_notes=request.POST.get('beverage_pairing_notes', ''),
            pairing_intensity=request.POST.get('pairing_intensity', 'medium'),
            is_optional='is_optional' in request.POST,
            supplement_charge=Decimal(request.POST.get('supplement_charge', 0)),
            order=int(request.POST.get('order', len(template.courses.all()) + 1)),
        )
        
        return redirect('menu_management:course_menu_template_detail', template_id=template_id)
    
    return render(request, 'menu_management/add_course_to_template.html', {'template': template})

@login_required
@user_passes_test(is_admin)
def create_course_menu_instance(request):
    """Create new course menu instance from template"""
    if request.method == 'POST':
        template = get_object_or_404(CourseMenuTemplate, template_id=request.POST.get('template_id'))
        
        # Calculate pricing
        pricing_tier = request.POST.get('pricing_tier', 'standard')
        price_per_person = template.price_per_person
        
        if pricing_tier != 'standard' and pricing_tier in template.price_tiers:
            price_per_person = Decimal(str(template.price_tiers[pricing_tier]['price']))
        
        # Create instance
        instance = CourseMenuInstance.objects.create(
            template=template,
            name=f"{template.name} - {request.POST.get('customer_name', 'Guest')}",
            table_number=request.POST.get('table_number'),
            customer_count=int(request.POST.get('customer_count')),
            final_price_per_person=price_per_person,
            total_price=price_per_person * int(request.POST.get('customer_count')),
            pricing_tier_applied=pricing_tier,
            dietary_requirements=json.loads(request.POST.get('dietary_requirements', '[]')),
            special_requests=request.POST.get('special_requests', ''),
            booking_date=request.POST.get('booking_date'),
            booking_time=request.POST.get('booking_time'),
            status='confirmed',
        )
        
        # Assign staff
        server_id = request.POST.get('server')
        if server_id:
            instance.server = User.objects.get(id=server_id)
        
        sommelier_id = request.POST.get('sommelier')
        if sommelier_id:
            instance.sommelier = User.objects.get(id=sommelier_id)
        
        chef_id = request.POST.get('assigned_chef')
        if chef_id:
            instance.assigned_chef = User.objects.get(id=chef_id)
        
        instance.save()
        
        # Create course instances
        courses = CourseDefinition.objects.filter(template=template).order_by('order', 'course_number')
        start_time = timezone.now()
        
        for i, course in enumerate(courses):
            scheduled_start = start_time + timedelta(minutes=i * template.pacing_interval)
            scheduled_completion = scheduled_start + timedelta(minutes=course.prep_time + course.plating_time)
            
            CourseInstance.objects.create(
                menu_instance=instance,
                course_definition=course,
                scheduled_start=scheduled_start,
                scheduled_completion=scheduled_completion,
                status='pending',
            )
        
        return redirect('menu_management:course_menu_instance_detail', instance_id=instance.instance_id)
    
    # Get available templates
    templates = CourseMenuTemplate.objects.filter(is_active=True)
    
    # Get available staff
    servers = User.objects.filter(is_staff=True).order_by('first_name')
    
    context = {
        'templates': templates,
        'servers': servers,
    }
    
    return render(request, 'menu_management/create_course_menu_instance.html', context)

@login_required
@user_passes_test(is_admin)
def course_menu_instances(request):
    """Manage course menu instances"""
    instances = CourseMenuInstance.objects.all().order_by('-created_at')
    
    # Apply filters
    status_filter = request.GET.get('status')
    date_filter = request.GET.get('date')
    search_filter = request.GET.get('search')
    
    if status_filter:
        instances = instances.filter(status=status_filter)
    
    if date_filter:
        instances = instances.filter(booking_date=date_filter)
    
    if search_filter:
        instances = instances.filter(
            models.Q(name__icontains=search_filter) |
            models.Q(table_number__icontains=search_filter)
        )
    
    # Calculate statistics
    total_instances = instances.count()
    booked_count = instances.filter(status='booked').count()
    confirmed_count = instances.filter(status='confirmed').count()
    in_progress_count = instances.filter(status='in_progress').count()
    completed_count = instances.filter(status='completed').count()
    cancelled_count = instances.filter(status='cancelled').count()
    
    context = {
        'instances': instances,
        'status_choices': CourseMenuInstance.STATUS_CHOICES,
        'total_instances': total_instances,
        'booked_count': booked_count,
        'confirmed_count': confirmed_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
    }
    
    return render(request, 'menu_management/course_menu_instances.html', context)

@login_required
@user_passes_test(is_admin)
def course_menu_instance_detail(request, instance_id):
    """Course menu instance detail and management"""
    instance = get_object_or_404(CourseMenuInstance, instance_id=instance_id)
    
    # Get course instances
    course_instances = instance.course_instances.select_related(
        'course_definition', 'kitchen_station', 'plating_station'
    ).order_by('scheduled_start')
    
    # Get available kitchen stations
    kitchen_stations = KitchenStation.objects.filter(is_active=True)
    
    context = {
        'instance': instance,
        'course_instances': course_instances,
        'kitchen_stations': kitchen_stations,
    }
    
    return render(request, 'menu_management/course_menu_instance_detail.html', context)

@login_required
@user_passes_test(is_admin)
def update_course_instance_status(request, instance_id):
    """Update course instance status"""
    if request.method == 'POST':
        instance = get_object_or_404(CourseInstance, instance_id=instance_id)
        
        new_status = request.POST.get('status')
        if new_status in ['pending', 'preparing', 'ready', 'served', 'skipped']:
            instance.status = new_status
            
            if new_status == 'ready':
                instance.actual_start = timezone.now()
            elif new_status == 'served':
                instance.actual_completion = timezone.now()
            
            instance.save()
            
            return JsonResponse({
                'success': True,
                'status': new_status,
                'actual_start': instance.actual_start.isoformat() if instance.actual_start else None,
                'actual_completion': instance.actual_completion.isoformat() if instance.actual_completion else None,
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
@user_passes_test(is_admin)
def wine_pairing_management(request):
    """Manage wine pairings for courses"""
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        course = get_object_or_404(CourseDefinition, course_id=course_id)
        
        pairing = WinePairing.objects.create(
            course_definition=course,
            wine_name=request.POST.get('wine_name'),
            wine_type=request.POST.get('wine_type'),
            region=request.POST.get('region'),
            vintage=int(request.POST.get('vintage')) if request.POST.get('vintage') else None,
            pairing_notes=request.POST.get('pairing_notes'),
            intensity_match=request.POST.get('intensity_match'),
            price_per_glass=Decimal(request.POST.get('price_per_glass')),
            price_per_bottle=Decimal(request.POST.get('price_per_bottle')),
            is_recommended='is_recommended' in request.POST,
        )
        
        return JsonResponse({
            'success': True,
            'pairing_id': str(pairing.pairing_id),
            'wine_name': pairing.wine_name,
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
@user_passes_test(is_admin)
def beverage_pairing_management(request):
    """Manage beverage pairings for courses"""
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        course = get_object_or_404(CourseDefinition, course_id=course_id)
        
        pairing = BeveragePairing.objects.create(
            course_definition=course,
            beverage_name=request.POST.get('beverage_name'),
            beverage_type=request.POST.get('beverage_type'),
            pairing_notes=request.POST.get('pairing_notes'),
            intensity_match=request.POST.get('intensity_match'),
            price_per_serving=Decimal(request.POST.get('price_per_serving')),
            is_recommended='is_recommended' in request.POST,
        )
        
        return JsonResponse({
            'success': True,
            'pairing_id': str(pairing.pairing_id),
            'beverage_name': pairing.beverage_name,
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
@user_passes_test(is_admin)
def course_menu_analytics(request):
    """Analytics for course menu performance"""
    # Get popular menu types with percentages
    popular_types = CourseMenuInstance.objects.values(
        'template__menu_type'
    ).annotate(count=Count('instance_id')).order_by('-count')[:10]
    
    # Calculate percentages for popular types
    popular_types_list = list(popular_types)
    if popular_types_list:
        max_count = popular_types_list[0]['count']
        for menu_type in popular_types_list:
            menu_type['percentage'] = (menu_type['count'] / max_count * 100) if max_count > 0 else 0
    else:
        max_count = 0
    
    # Get dietary preferences (SQLite compatible)
    total_instances = CourseMenuInstance.objects.count()
    vegetarian_count = sum(1 for instance in CourseMenuInstance.objects.all() 
                          if 'vegetarian' in instance.dietary_requirements)
    vegan_count = sum(1 for instance in CourseMenuInstance.objects.all() 
                      if 'vegan' in instance.dietary_requirements)
    gluten_free_count = sum(1 for instance in CourseMenuInstance.objects.all() 
                           if 'gluten_free' in instance.dietary_requirements)
    no_restrictions_count = total_instances - vegetarian_count - vegan_count - gluten_free_count
    
    # Calculate dietary percentages
    vegetarian_percentage = (vegetarian_count / total_instances * 100) if total_instances > 0 else 0
    vegan_percentage = (vegan_count / total_instances * 100) if total_instances > 0 else 0
    gluten_free_percentage = (gluten_free_count / total_instances * 100) if total_instances > 0 else 0
    no_restrictions_percentage = (no_restrictions_count / total_instances * 100) if total_instances > 0 else 0
    
    dietary_stats = {
        'total': total_instances,
        'vegetarian': vegetarian_count,
        'vegan': vegan_count,
        'gluten_free': gluten_free_count,
        'no_restrictions': no_restrictions_count,
        'vegetarian_percentage': vegetarian_percentage,
        'vegan_percentage': vegan_percentage,
        'gluten_free_percentage': gluten_free_percentage,
        'no_restrictions_percentage': no_restrictions_percentage,
    }
    
    # Get revenue by menu type with percentages
    revenue_by_type = CourseMenuInstance.objects.values(
        'template__menu_type'
    ).annotate(
        total_revenue=Sum('total_price'),
        avg_price=Avg('final_price_per_person')
    ).order_by('-total_revenue')
    
    # Calculate revenue percentages
    revenue_by_type_list = list(revenue_by_type)
    if revenue_by_type_list:
        max_revenue = revenue_by_type_list[0]['total_revenue']
        for revenue in revenue_by_type_list:
            revenue['revenue_percentage'] = (revenue['total_revenue'] / max_revenue * 100) if max_revenue > 0 else 0
    else:
        max_revenue = 0
    
    # Get completion rates
    completion_stats = CourseMenuInstance.objects.aggregate(
        total=Count('instance_id'),
        completed=Count('instance_id', filter=Q(status='completed')),
        cancelled=Count('instance_id', filter=Q(status='cancelled')),
    )
    
    # Calculate in progress count
    in_progress_count = completion_stats['total'] - completion_stats['completed'] - completion_stats['cancelled']
    
    completion_rate = 0
    if completion_stats['total'] > 0:
        completion_rate = (completion_stats['completed'] / completion_stats['total']) * 100
    
    context = {
        'popular_types': popular_types_list,
        'dietary_stats': dietary_stats,
        'revenue_by_type': revenue_by_type_list,
        'completion_stats': completion_stats,
        'completion_rate': completion_rate,
        'in_progress_count': in_progress_count,
    }
    
    return render(request, 'menu_management/course_menu_analytics.html', context)
