from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, date, time, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Table, TableReservation, VenueReservation, ReservationSettings

def reservation_dashboard(request):
    """Main reservation dashboard for customers"""
    if not request.user.is_authenticated:
        return redirect('customer_login')
    
    # Get user's reservations
    table_reservations = TableReservation.objects.filter(customer=request.user).order_by('date', 'time')
    venue_reservations = VenueReservation.objects.filter(customer=request.user).order_by('date', 'start_time')
    
    # Get available tables for quick booking
    available_tables = Table.objects.filter(is_available=True).order_by('table_number')
    
    context = {
        'table_reservations': table_reservations,
        'venue_reservations': venue_reservations,
        'available_tables': available_tables,
    }
    
    return render(request, 'reservations/reservation_dashboard.html', context)

@login_required
def create_table_reservation(request):
    """Create a new table reservation"""
    if request.method == 'POST':
        try:
            # Get form data
            table_id = request.POST.get('table')
            reservation_date = request.POST.get('date')
            reservation_time = request.POST.get('time')
            party_size = int(request.POST.get('party_size'))
            occasion = request.POST.get('occasion', '')
            special_requests = request.POST.get('special_requests', '')
            
            # Validate date and time
            reservation_datetime = datetime.strptime(f"{reservation_date} {reservation_time}", "%Y-%m-%d %H:%M")
            if reservation_datetime < timezone.now():
                messages.error(request, 'Cannot make reservations for past dates.')
                return redirect('reservation_dashboard')
            
            # Get table
            table = get_object_or_404(Table, id=table_id)
            
            # Check if table is available
            existing_reservation = TableReservation.objects.filter(
                table=table,
                date=reservation_date,
                time=reservation_time,
                status__in=['pending', 'confirmed']
            ).first()
            
            if existing_reservation:
                messages.error(request, f'Table {table.table_number} is already booked at that time.')
                return redirect('reservation_dashboard')
            
            # Create reservation
            reservation = TableReservation.objects.create(
                table=table,
                customer=request.user,
                date=reservation_date,
                time=reservation_time,
                party_size=party_size,
                occasion=occasion,
                special_requests=special_requests,
                status='confirmed' if ReservationSettings.objects.first().auto_confirmation else 'pending'
            )
            
            messages.success(request, f'Table reservation confirmed! Your confirmation code is {reservation.confirmation_code}')
            return redirect('reservation_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error creating reservation: {str(e)}')
            return redirect('reservation_dashboard')
    
    # GET request - show form
    available_tables = Table.objects.filter(is_available=True).order_by('table_number')
    return render(request, 'reservations/create_table_reservation.html', {'tables': available_tables})

@login_required
def create_venue_reservation(request):
    """Create a new venue reservation"""
    if request.method == 'POST':
        try:
            # Get form data
            event_name = request.POST.get('event_name')
            event_type = request.POST.get('event_type')
            event_date = request.POST.get('date')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            expected_guests = int(request.POST.get('expected_guests'))
            catering_options = request.POST.get('catering_options')
            setup_requirements = request.POST.get('setup_requirements', '')
            budget_range = request.POST.get('budget_range')
            contact_phone = request.POST.get('contact_phone')
            contact_email = request.POST.get('contact_email')
            
            # Validate date and time
            event_datetime = datetime.strptime(f"{event_date} {start_time}", "%Y-%m-%d %H:%M")
            if event_datetime < timezone.now():
                messages.error(request, 'Cannot book venue for past dates.')
                return redirect('reservation_dashboard')
            
            # Check for venue availability
            existing_booking = VenueReservation.objects.filter(
                date=event_date,
                status__in=['pending', 'confirmed', 'deposit_paid', 'fully_paid']
            ).first()
            
            if existing_booking:
                messages.error(request, 'Venue is already booked for this date.')
                return redirect('reservation_dashboard')
            
            # Create venue reservation
            reservation = VenueReservation.objects.create(
                customer=request.user,
                event_name=event_name,
                event_type=event_type,
                date=event_date,
                start_time=start_time,
                end_time=end_time,
                expected_guests=expected_guests,
                catering_options=catering_options,
                setup_requirements=setup_requirements,
                budget_range=budget_range,
                contact_phone=contact_phone,
                contact_email=contact_email,
                status='pending'
            )
            
            messages.success(request, f'Venue booking submitted! Your confirmation code is {reservation.confirmation_code}. We will contact you soon.')
            return redirect('reservation_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error creating venue booking: {str(e)}')
            return redirect('reservation_dashboard')
    
    # GET request - show form
    return render(request, 'reservations/create_venue_reservation.html')

@login_required
def cancel_reservation(request, reservation_type, reservation_id):
    """Cancel a reservation"""
    try:
        if reservation_type == 'table':
            reservation = get_object_or_404(TableReservation, id=reservation_id, customer=request.user)
            if reservation.status in ['pending', 'confirmed']:
                reservation.status = 'cancelled'
                reservation.save()
                messages.success(request, 'Table reservation cancelled successfully.')
            else:
                messages.error(request, 'Cannot cancel this reservation.')
                
        elif reservation_type == 'venue':
            reservation = get_object_or_404(VenueReservation, id=reservation_id, customer=request.user)
            if reservation.status in ['inquiry', 'pending', 'confirmed']:
                reservation.status = 'cancelled'
                reservation.save()
                messages.success(request, 'Venue booking cancelled successfully.')
            else:
                messages.error(request, 'Cannot cancel this booking.')
        
        return redirect('reservation_dashboard')
        
    except Exception as e:
        messages.error(request, f'Error cancelling reservation: {str(e)}')
        return redirect('reservation_dashboard')

@login_required
def reservation_detail(request, reservation_type, reservation_id):
    """View reservation details"""
    try:
        if reservation_type == 'table':
            reservation = get_object_or_404(TableReservation, id=reservation_id, customer=request.user)
            template = 'reservations/table_reservation_detail.html'
            
        elif reservation_type == 'venue':
            reservation = get_object_or_404(VenueReservation, id=reservation_id, customer=request.user)
            template = 'reservations/venue_reservation_detail.html'
        
        return render(request, template, {'reservation': reservation})
        
    except Exception as e:
        messages.error(request, f'Error loading reservation details: {str(e)}')
        return redirect('reservation_dashboard')
