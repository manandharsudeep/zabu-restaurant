from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
import json

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
@user_passes_test(is_admin)
def user_management_frontend(request):
    """Frontend user management interface"""
    
    # Get user statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    new_this_week = User.objects.filter(
        date_joined__gte=timezone.now() - timedelta(days=7)
    ).count()
    active_now = User.objects.filter(
        last_login__gte=timezone.now() - timedelta(hours=1)
    ).count()
    
    # Get all users with their details
    users = User.objects.all().order_by('-date_joined')
    
    context = {
        'users': users,
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
        'new_this_week': new_this_week,
        'active_now': active_now,
    }
    
    return render(request, 'user_management_frontend.html', context)

@login_required
@user_passes_test(is_admin)
def create_user_frontend(request):
    """Create new user via frontend interface"""
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            first_name = request.POST.get('firstName')
            last_name = request.POST.get('lastName')
            password = request.POST.get('password')
            user_role = request.POST.get('userRole')
            is_active = request.POST.get('isActive') == 'on'
            
            # Validate data
            if not username or not password:
                return JsonResponse({'success': False, 'message': 'Username and password are required'})
            
            if User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'message': 'Username already exists'})
            
            if len(password) < 8:
                return JsonResponse({'success': False, 'message': 'Password must be at least 8 characters long'})
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Set permissions
            user.is_active = is_active
            if user_role == 'staff':
                user.is_staff = True
            elif user_role == 'admin':
                user.is_staff = True
                user.is_superuser = True
            
            user.save()
            
            return JsonResponse({'success': True, 'message': f'User {first_name} {last_name} created successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_admin)
def update_user_frontend(request, user_id):
    """Update user via frontend interface"""
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, id=user_id)
            
            email = request.POST.get('email')
            first_name = request.POST.get('firstName')
            last_name = request.POST.get('lastName')
            user_role = request.POST.get('userRole')
            is_active = request.POST.get('isActive') == 'on'
            
            # Update user
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.is_active = is_active
            
            # Set permissions
            if user_role == 'staff':
                user.is_staff = True
                user.is_superuser = False
            elif user_role == 'admin':
                user.is_staff = True
                user.is_superuser = True
            else:
                user.is_staff = False
                user.is_superuser = False
            
            user.save()
            
            return JsonResponse({'success': True, 'message': f'User {first_name} {last_name} updated successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_admin)
def delete_user_frontend(request, user_id):
    """Delete user via frontend interface"""
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, id=user_id)
            
            # Prevent deletion of superusers
            if user.is_superuser:
                return JsonResponse({'success': False, 'message': 'Cannot delete superuser accounts'})
            
            user_name = f"{user.first_name} {user.last_name}"
            user.delete()
            
            return JsonResponse({'success': True, 'message': f'User {user_name} deleted successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_admin)
def change_password_frontend(request, user_id):
    """Change user password via frontend interface"""
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, id=user_id)
            new_password = request.POST.get('password')
            
            if not new_password or len(new_password) < 8:
                return JsonResponse({'success': False, 'message': 'Password must be at least 8 characters long'})
            
            user.set_password(new_password)
            user.save()
            
            return JsonResponse({'success': True, 'message': f'Password changed for {user.first_name} {user.last_name}'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_admin)
def toggle_user_status_frontend(request, user_id):
    """Toggle user status via frontend interface"""
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, id=user_id)
            
            # Prevent deactivation of superusers
            if user.is_superuser and user.is_active:
                return JsonResponse({'success': False, 'message': 'Cannot deactivate superuser accounts'})
            
            user.is_active = not user.is_active
            user.save()
            
            status = "activated" if user.is_active else "deactivated"
            return JsonResponse({'success': True, 'message': f'User {user.first_name} {user.last_name} {status}'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})
