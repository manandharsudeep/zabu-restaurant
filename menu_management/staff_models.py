from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import uuid

class StaffProfile(models.Model):
    """Extended staff profile information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=20, blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)
    hire_date = models.DateField()
    position = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_full_time = models.BooleanField(default=False)
    certifications = models.TextField(blank=True, help_text="List of certifications and training")
    skills = models.TextField(blank=True, help_text="Skills and competencies")
    availability_notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.position}"

class ShiftTemplate(models.Model):
    """Shift templates for scheduling"""
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_duration = models.IntegerField(default=30, help_text="Break duration in minutes")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"
    
    @property
    def duration_hours(self):
        start = timezone.datetime.combine(timezone.date.today(), self.start_time)
        end = timezone.datetime.combine(timezone.date.today(), self.end_time)
        if end < start:
            end += timezone.timedelta(days=1)
        return (end - start).total_seconds() / 3600

class Schedule(models.Model):
    """Staff schedules"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('active', 'Active'),
        ('completed', 'Completed'),
    ]
    
    schedule_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='schedules')
    shift_template = models.ForeignKey(ShiftTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_duration = models.IntegerField(default=30)
    station = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    is_overtime = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['staff', 'date', 'start_time']
    
    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.date} ({self.start_time})"
    
    @property
    def duration_hours(self):
        start = timezone.datetime.combine(self.date, self.start_time)
        end = timezone.datetime.combine(self.date, self.end_time)
        if end < start:
            end += timezone.timedelta(days=1)
        return (end - start).total_seconds() / 3600 - (self.break_duration / 60)
    
    @property
    def labor_cost(self):
        if self.staff.hourly_rate:
            return self.duration_hours * self.staff.hourly_rate
        return 0

class ShiftSwap(models.Model):
    """Shift swap requests"""
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    swap_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='swap_requests')
    requesting_staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='swap_requests')
    target_staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='swap_assignments')
    swap_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    notes = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Swap: {self.requesting_staff.user.get_full_name()} -> {self.target_staff.user.get_full_name()}"

class TimeOffRequest(models.Model):
    """Time off and leave requests"""
    REQUEST_TYPES = [
        ('vacation', 'Vacation'),
        ('sick', 'Sick Leave'),
        ('personal', 'Personal Day'),
        ('bereavement', 'Bereavement'),
        ('jury_duty', 'Jury Duty'),
        ('military', 'Military Duty'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    request_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='time_off_requests')
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    notes = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.get_request_type_display()} ({self.start_date})"
    
    @property
    def duration_days(self):
        return (self.end_date - self.start_date).days + 1

class Task(models.Model):
    """Task management system"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    TASK_TYPES = [
        ('opening', 'Opening Duties'),
        ('mid_shift', 'Mid-Shift Duties'),
        ('closing', 'Closing Duties'),
        ('maintenance', 'Maintenance'),
        ('cleaning', 'Cleaning'),
        ('inventory', 'Inventory'),
        ('training', 'Training'),
        ('other', 'Other'),
    ]
    
    task_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(StaffProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tasks')
    location = models.CharField(max_length=100, blank=True)
    station = models.CharField(max_length=100, blank=True)
    due_date = models.DateTimeField()
    estimated_duration = models.IntegerField(help_text="Estimated duration in minutes")
    actual_duration = models.IntegerField(null=True, blank=True, help_text="Actual duration in minutes")
    completion_notes = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    @property
    def is_overdue(self):
        return self.due_date < timezone.now() and self.status not in ['completed', 'cancelled']

class TaskChecklist(models.Model):
    """Task checklists for complex tasks"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='checklist_items')
    item_text = models.CharField(max_length=200)
    is_completed = models.BooleanField(default=False)
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.item_text} - {'✓' if self.is_completed else '○'}"

class Communication(models.Model):
    """Internal communication system"""
    MESSAGE_TYPES = [
        ('broadcast', 'Broadcast'),
        ('direct', 'Direct Message'),
        ('announcement', 'Announcement'),
        ('emergency', 'Emergency'),
        ('shift_note', 'Shift Note'),
        ('handoff', 'Handoff Note'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    subject = models.CharField(max_length=200)
    content = models.TextField()
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    recipients = models.ManyToManyField(User, related_name='received_messages', blank=True)
    all_staff = models.BooleanField(default=False, help_text="Send to all active staff")
    all_managers = models.BooleanField(default=False, help_text="Send to all managers")
    requires_read_receipt = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_message_type_display()}: {self.subject}"

class MessageReadReceipt(models.Model):
    """Track message read receipts"""
    message = models.ForeignKey(Communication, on_delete=models.CASCADE, related_name='read_receipts')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user']
    
    def __str__(self):
        return f"{self.user.get_full_name()} read: {self.message.subject}"

class DailyBriefing(models.Model):
    """Daily briefing and pre-shift meeting notes"""
    briefing_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(unique=True)
    shift = models.CharField(max_length=50, help_text="Morning/Evening/Night")
    presenter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    weather_conditions = models.CharField(max_length=100, blank=True)
    special_events = models.TextField(blank=True)
    staff_attendance = models.TextField(blank=True)
    equipment_status = models.TextField(blank=True)
    inventory_notes = models.TextField(blank=True)
    customer_feedback = models.TextField(blank=True)
    safety_notes = models.TextField(blank=True)
    goals_focus = models.TextField(blank=True)
    announcements = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Briefing: {self.date} - {self.shift}"

class ManagerLog(models.Model):
    """Manager log book for daily operations"""
    LOG_TYPES = [
        ('daily_summary', 'Daily Summary'),
        ('incident', 'Incident Report'),
        ('complaint', 'Customer Complaint'),
        ('compliment', 'Customer Compliment'),
        ('maintenance', 'Maintenance Issue'),
        ('staff_issue', 'Staff Issue'),
        ('inventory', 'Inventory Issue'),
        ('sales', 'Sales Performance'),
        ('other', 'Other'),
    ]
    
    log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    log_type = models.CharField(max_length=20, choices=LOG_TYPES)
    date = models.DateField()
    time = models.TimeField()
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    action_taken = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_notes = models.TextField(blank=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_log_type_display()}: {self.title} ({self.date})"
