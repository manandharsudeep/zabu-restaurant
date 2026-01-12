from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from decimal import Decimal
import json

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
@user_passes_test(is_admin)
def user_management_dashboard(request):
    """Main user management dashboard"""
    users = User.objects.all().order_by('-date_joined')
    
    # User statistics
    total_users = users.count()
    active_users = users.filter(is_active=True).count()
    staff_users = users.filter(is_staff=True).count()
    superusers = users.filter(is_superuser=True).count()
    recent_users = users.filter(date_joined__gte=timezone.now() - timezone.timedelta(days=7)).count()
    
    context = {
        'users': users,
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
        'superusers': superusers,
        'recent_users': recent_users,
    }
    
    return render(request, 'orders/user_management_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def user_details(request, user_id):
    """View detailed user information"""
    user = get_object_or_404(User, id=user_id)
    
    # Get or create user profile
    from orders.models import UserProfile
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Get user activity (you can expand this with actual activity tracking)
    user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone': profile.phone,
        'is_active': user.is_active,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'date_joined': user.date_joined,
        'last_login': user.last_login,
        'full_name': user.get_full_name(),
    }
    
    # Get user orders (if you have order models)
    try:
        from orders.models import Order
        user_orders = Order.objects.filter(user=user).order_by('-created_at')[:10]
        order_count = Order.objects.filter(user=user).count()
    except:
        user_orders = []
        order_count = 0
    
    # Get user meal passes (if you have meal pass models)
    try:
        from orders.models import MealPassSubscription
        user_meal_passes = MealPassSubscription.objects.filter(user=user).order_by('-created_at')[:5]
        meal_pass_count = MealPassSubscription.objects.filter(user=user).count()
    except:
        user_meal_passes = []
        meal_pass_count = 0
    
    context = {
        'user': user,
        'user_data': user_data,
        'user_orders': user_orders,
        'order_count': order_count,
        'user_meal_passes': user_meal_passes,
        'meal_pass_count': meal_pass_count,
    }
    
    return render(request, 'orders/user_details.html', context)

@login_required
@user_passes_test(is_admin)
def edit_user(request, user_id):
    """Edit user details"""
    user = get_object_or_404(User, id=user_id)
    
    # Get or create user profile
    from orders.models import UserProfile
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        # Update user details
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        
        # Update phone number
        phone = request.POST.get('phone', '')
        if phone:
            profile.phone = phone
            profile.save()
        
        # Update permissions
        user.is_active = request.POST.get('is_active') == 'on'
        user.is_staff = request.POST.get('is_staff') == 'on'
        user.is_superuser = request.POST.get('is_superuser') == 'on'
        
        user.save()
        
        messages.success(request, f'User {user.username} updated successfully!')
        return redirect('orders:user_details', user_id=user.id)
    
    return render(request, 'menu_management/edit_user.html', {'user': user})

@login_required
@user_passes_test(is_admin)
def change_user_password(request, user_id):
    """Change user password"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password and confirm_password:
            if password == confirm_password:
                if len(password) >= 8:
                    user.set_password(password)
                    user.save()
                    
                    # Update session to prevent logout
                    update_session_auth_hash(request, user)
                    
                    messages.success(request, f'Password for {user.username} changed successfully!')
                else:
                    messages.error(request, 'Password must be at least 8 characters long.')
            else:
                messages.error(request, 'Passwords do not match.')
        else:
            messages.error(request, 'Please provide both password and confirmation.')
        
        return redirect('orders:user_details', user_id=user.id)
    
    return render(request, 'orders/change_user_password.html', {'user': user})

@login_required
@user_passes_test(is_admin)
def create_user(request):
    """Create a new user"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Set additional fields
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            
            # Set permissions
            user.is_active = request.POST.get('is_active') == 'on'
            user.is_staff = request.POST.get('is_staff') == 'on'
            user.is_superuser = request.POST.get('is_superuser') == 'on'
            
            user.save()
            
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('orders:user_details', user_id=user.id)
    else:
        form = UserCreationForm()
    
    return render(request, 'orders/create_user.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    """Delete a user"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully!')
        return redirect('orders:user_management_dashboard')
    
    return render(request, 'orders/delete_user.html', {'user': user})

@login_required
@user_passes_test(is_admin)
def toggle_user_status(request, user_id):
    """Toggle user active status"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        
        status = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'User {user.username} {status} successfully!')
        
        return JsonResponse({
            'success': True,
            'is_active': user.is_active,
            'message': f'User {user.username} {status} successfully!'
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_admin)
@csrf_exempt
def update_user_details(request, user_id):
    """Update user details via AJAX"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Update fields
            if 'first_name' in data:
                user.first_name = data['first_name']
            if 'last_name' in data:
                user.last_name = data['last_name']
            if 'email' in data:
                user.email = data['email']
            if 'is_active' in data:
                user.is_active = data['is_active']
            if 'is_staff' in data:
                user.is_staff = data['is_staff']
            if 'is_superuser' in data:
                user.is_superuser = data['is_superuser']
            
            user.save()
            
            return JsonResponse({
                'success': True,
                'message': f'User {user.username} updated successfully!',
                'user_data': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_active': user.is_active,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                    'full_name': user.get_full_name(),
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error updating user: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def my_profile(request):
    """View and edit own profile"""
    if request.method == 'POST':
        # Update own profile
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        messages.success(request, 'Your profile has been updated!')
        return redirect('orders:my_profile')
    
    # Get user's orders and meal passes
    try:
        from orders.models import Order, MealPassSubscription
        user_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
        user_meal_passes = MealPassSubscription.objects.filter(user=request.user).order_by('-created_at')[:3]
    except:
        user_orders = []
        user_meal_passes = []
    
    context = {
        'user_orders': user_orders,
        'user_meal_passes': user_meal_passes,
    }
    
    return render(request, 'orders/my_profile.html', context)

@login_required
def change_my_password(request):
    """Change own password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('orders:my_profile')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'orders/change_my_password.html', {'form': form})
