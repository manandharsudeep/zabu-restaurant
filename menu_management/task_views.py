from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Task, StaffProfile
from .forms import TaskForm, TaskFilterForm
from django.contrib.auth.models import User

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
@user_passes_test(is_admin)
def create_task(request):
    """Create a new task"""
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_by = request.user
            task.save()
            
            messages.success(request, f'Task "{task.title}" created successfully!')
            return redirect('menu_management:task_management')
    else:
        form = TaskForm(initial={
            'due_date': timezone.now() + timezone.timedelta(hours=4),
            'estimated_duration': 30,
            'priority': 'medium',
            'status': 'pending',
            'task_type': 'other'
        })
    
    return render(request, 'menu_management/create_task.html', {
        'form': form,
        'title': 'Create Task'
    })

@login_required
@user_passes_test(is_admin)
def task_detail(request, task_id):
    """View task details"""
    task = get_object_or_404(Task, task_id=task_id)
    
    # Get task history
    task_history = []
    if task.completed_at:
        task_history.append({
            'action': 'Completed',
            'timestamp': task.completed_at,
            'user': task.completed_by.get_full_name() if task.completed_by else 'Unknown',
            'notes': task.completion_notes
        })
    
    return render(request, 'menu_management/task_detail.html', {
        'task': task,
        'task_history': task_history,
        'title': f'Task Details - {task.title}'
    })

@login_required
@user_passes_test(is_admin)
def edit_task(request, task_id):
    """Edit an existing task"""
    task = get_object_or_404(Task, task_id=task_id)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            updated_task = form.save()
            
            # If task is being marked as completed, set completion details
            if updated_task.status == 'completed' and task.status != 'completed':
                updated_task.completed_at = timezone.now()
                updated_task.completed_by = request.user
                updated_task.save()
            
            messages.success(request, f'Task "{updated_task.title}" updated successfully!')
            return redirect('menu_management:task_detail', task_id=task_id)
    else:
        form = TaskForm(instance=task)
    
    return render(request, 'menu_management/edit_task.html', {
        'form': form,
        'task': task,
        'title': f'Edit Task - {task.title}'
    })

@login_required
@user_passes_test(is_admin)
def delete_task(request, task_id):
    """Delete a task"""
    task = get_object_or_404(Task, task_id=task_id)
    
    if request.method == 'POST':
        task_title = task.title
        task.delete()
        messages.success(request, f'Task "{task_title}" deleted successfully!')
        return redirect('menu_management:task_management')
    
    return render(request, 'menu_management/delete_task.html', {
        'task': task,
        'title': f'Delete Task - {task.title}'
    })

@login_required
@user_passes_test(is_admin)
def update_task_status(request, task_id):
    """Update task status via AJAX"""
    task = get_object_or_404(Task, task_id=task_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        completion_notes = request.POST.get('completion_notes', '')
        
        if new_status in dict(Task.STATUS_CHOICES):
            old_status = task.status
            task.status = new_status
            
            # If task is being marked as completed
            if new_status == 'completed' and old_status != 'completed':
                task.completed_at = timezone.now()
                task.completed_by = request.user
                if completion_notes:
                    task.completion_notes = completion_notes
            
            task.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Task status updated to {task.get_status_display()}',
                'new_status': task.get_status_display(),
                'new_status_class': f'status-{new_status.replace("_", "-")}'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid status'
            })
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'})

@login_required
@user_passes_test(is_admin)
def task_dashboard(request):
    """Global task dashboard accessible from main module"""
    status = request.GET.get('status', '')
    assigned_to = request.GET.get('assigned_to', '')
    priority = request.GET.get('priority', '')
    task_type = request.GET.get('task_type', '')
    
    tasks = Task.objects.select_related(
        'assigned_to', 'assigned_to__user', 'assigned_by'
    ).order_by('-created_at')
    
    # Apply filters
    if status:
        tasks = tasks.filter(status=status)
    if assigned_to:
        tasks = tasks.filter(assigned_to_id=assigned_to)
    if priority:
        tasks = tasks.filter(priority=priority)
    if task_type:
        tasks = tasks.filter(task_type=task_type)
    
    # Get statistics
    total_tasks = tasks.count()
    pending_tasks = tasks.filter(status='pending').count()
    in_progress_tasks = tasks.filter(status='in_progress').count()
    completed_tasks = tasks.filter(status='completed').count()
    overdue_tasks = tasks.filter(
        due_date__lt=timezone.now(),
        status__in=['pending', 'in_progress']
    ).count()
    
    # Pagination
    paginator = Paginator(tasks, 20)
    page = request.GET.get('page')
    tasks_page = paginator.get_page(page)
    
    # Get filter options
    active_staff = StaffProfile.objects.filter(is_active=True)
    
    context = {
        'tasks_page': tasks_page,
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
        'task_types': Task.TASK_TYPES,
        'selected_status': status,
        'selected_assigned_to': assigned_to,
        'selected_priority': priority,
        'selected_task_type': task_type,
        'active_staff': active_staff,
        'title': 'Task Dashboard'
    }
    
    return render(request, 'menu_management/task_dashboard.html', context)
