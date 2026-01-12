from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from .models import Vendor
from django.db import IntegrityError

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
@user_passes_test(is_admin)
def create_vendor(request):
    """Create a new vendor"""
    if request.method == 'POST':
        name = request.POST.get('name')
        contact_person = request.POST.get('contact_person')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        vendor_code = request.POST.get('vendor_code')
        is_preferred = request.POST.get('is_preferred') == 'on'
        lead_time_days = request.POST.get('lead_time_days', 2)
        payment_terms = request.POST.get('payment_terms', 'Net 30')
        notes = request.POST.get('notes', '')
        
        # Validation
        if not all([name, contact_person, email, phone, address, vendor_code]):
            messages.error(request, 'All required fields must be filled out.')
            return render(request, 'menu_management/create_vendor.html', {
                'form_data': request.POST
            })
        
        try:
            # Create vendor
            vendor = Vendor.objects.create(
                name=name,
                contact_person=contact_person,
                email=email,
                phone=phone,
                address=address,
                vendor_code=vendor_code,
                is_preferred=is_preferred,
                lead_time_days=lead_time_days,
                payment_terms=payment_terms,
                notes=notes
            )
            
            messages.success(request, f'Vendor "{name}" created successfully!')
            return redirect('menu_management:inventory_dashboard')
            
        except IntegrityError:
            messages.error(request, 'Vendor code already exists. Please use a different vendor code.')
            return render(request, 'menu_management/create_vendor.html', {
                'form_data': request.POST
            })
        except Exception as e:
            messages.error(request, f'Error creating vendor: {str(e)}')
            return render(request, 'menu_management/create_vendor.html', {
                'form_data': request.POST
            })
    
    return render(request, 'menu_management/create_vendor.html', {
        'form_data': {}
    })

@login_required
@user_passes_test(is_admin)
def vendor_list(request):
    """List all vendors"""
    vendors = Vendor.objects.all().order_by('name')
    return render(request, 'menu_management/vendor_list.html', {
        'vendors': vendors
    })
