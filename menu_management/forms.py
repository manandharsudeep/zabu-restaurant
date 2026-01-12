from django import forms
from django.utils import timezone
from .models import Task, StaffProfile

class TaskForm(forms.ModelForm):
    """Form for creating and editing tasks"""
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'task_type', 'priority', 'status',
            'assigned_to', 'location', 'station', 'due_date', 'estimated_duration'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter task title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter task description'
            }),
            'task_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-control'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter location (optional)'
            }),
            'station': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter station (optional)'
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'estimated_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 480,
                'placeholder': 'Duration in minutes'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter staff profiles to only active ones
        self.fields['assigned_to'].queryset = StaffProfile.objects.filter(is_active=True)
        self.fields['assigned_to'].empty_label = 'Select staff member'
        
        # Set default due date to 4 hours from now if not provided
        if not self.instance.pk:
            self.fields['due_date'].initial = timezone.now() + timezone.timedelta(hours=4)
    
    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now():
            raise forms.ValidationError('Due date cannot be in the past.')
        return due_date
    
    def clean_estimated_duration(self):
        duration = self.cleaned_data.get('estimated_duration')
        if duration and (duration < 1 or duration > 480):
            raise forms.ValidationError('Duration must be between 1 and 480 minutes.')
        return duration

class TaskFilterForm(forms.Form):
    """Form for filtering tasks"""
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + Task.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    priority = forms.ChoiceField(
        choices=[('', 'All Priorities')] + Task.PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    task_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Task.TASK_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    assigned_to = forms.ModelChoiceField(
        queryset=StaffProfile.objects.filter(is_active=True),
        empty_label='All Staff',
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

class TaskStatusUpdateForm(forms.Form):
    """Form for updating task status"""
    
    status = forms.ChoiceField(
        choices=Task.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    completion_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add completion notes (optional)'
        })
    )
