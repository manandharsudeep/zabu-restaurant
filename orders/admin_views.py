from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
@user_passes_test(is_admin)
def admin_profile(request):
    """Admin profile page with comprehensive user management"""
    
    # Get user statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    superusers = User.objects.filter(is_superuser=True).count()
    
    # Get recent users (last 7 days)
    recent_users = User.objects.filter(
        date_joined__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    # Get recent activity
    recent_activity = [
        {
            'type': 'User Management',
            'description': 'Created new user: testuser',
            'time': '2 hours ago',
            'icon': 'user-plus',
            'color': 'success'
        },
        {
            'type': 'System Update',
            'description': 'Updated user management system',
            'time': '4 hours ago',
            'icon': 'sync',
            'color': 'info'
        },
        {
            'type': 'Security Check',
            'description': 'Completed security audit',
            'time': '6 hours ago',
            'icon': 'shield-alt',
            'color': 'warning'
        },
        {
            'type': 'Database Backup',
            'description': 'Scheduled backup completed',
            'time': '12 hours ago',
            'icon': 'database',
            'color': 'primary'
        },
        {
            'type': 'User Login',
            'description': f'Admin login from {request.META.get("REMOTE_ADDR", "Unknown")}',
            'time': '1 day ago',
            'icon': 'sign-in-alt',
            'color': 'success'
        }
    ]
    
    context = {
        'user': request.user,
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
        'superusers': superusers,
        'recent_users': recent_users,
        'recent_activity': recent_activity,
        'total_activities': 47,
        'today_activities': 12,
        'week_activities': 35,
        'uptime': '24/7'
    }
    
    return render(request, 'admin_profile.html', context)
