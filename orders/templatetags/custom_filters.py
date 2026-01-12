from django import template
import re

register = template.Library()

@register.filter
def slugify(value):
    """
    Convert string to slug format
    """
    value = str(value)
    # Convert to lowercase and replace spaces with hyphens
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-')
