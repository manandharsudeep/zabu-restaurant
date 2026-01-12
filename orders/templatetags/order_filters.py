from django import template

register = template.Library()

@register.filter
def status_color(status):
    colors = {
        'pending': 'warning',
        'confirmed': 'info',
        'preparing': 'primary',
        'ready': 'success',
        'completed': 'secondary',
        'cancelled': 'danger'
    }
    return colors.get(status, 'secondary')

@register.filter
def priority_color(priority):
    colors = {
        'low': 'secondary',
        'medium': 'info',
        'high': 'warning',
        'urgent': 'danger'
    }
    return colors.get(priority, 'secondary')
