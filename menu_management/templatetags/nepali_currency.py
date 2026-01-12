from django import template
from django.conf import settings
from decimal import Decimal
import locale

register = template.Library()

@register.filter
def nepali_currency(value):
    """Format currency in Nepali Rupees format"""
    try:
        # Convert to Decimal if it's not already
        if isinstance(value, str):
            value = Decimal(value)
        elif not isinstance(value, Decimal):
            value = Decimal(str(value))
        
        # Format the number with Nepali style
        if value >= 100000:  # For lakhs and above
            # Convert to lakhs for better readability
            lakhs = value / 100000
            if lakhs >= 100:  # For crores and above
                crores = lakhs / 100
                if crores >= 100:  # For arabs and above
                    arabs = crores / 100
                    return f"{settings.CURRENCY_SYMBOL} {arabs:,.2f} Arab"
                else:
                    return f"{settings.CURRENCY_SYMBOL} {crores:,.2f} Crore"
            else:
                return f"{settings.CURRENCY_SYMBOL} {lakhs:,.2f} Lakh"
        else:
            # Regular formatting for smaller amounts
            formatted = f"{value:,.2f}"
            return f"{settings.CURRENCY_SYMBOL} {formatted}"
            
    except (ValueError, TypeError):
        # Fallback to simple formatting
        return f"{settings.CURRENCY_SYMBOL} {value}"

@register.filter
def nepali_currency_simple(value):
    """Simple Nepali currency formatting without large number abbreviations"""
    try:
        # Convert to Decimal if it's not already
        if isinstance(value, str):
            value = Decimal(value)
        elif not isinstance(value, Decimal):
            value = Decimal(str(value))
        
        # Format with standard thousand separators
        formatted = f"{value:,.2f}"
        return f"{settings.CURRENCY_SYMBOL} {formatted}"
        
    except (ValueError, TypeError):
        # Fallback to simple formatting
        return f"{settings.CURRENCY_SYMBOL} {value}"

@register.filter
def nepali_number(value):
    """Format numbers in Nepali style"""
    try:
        # Convert to Decimal if it's not already
        if isinstance(value, str):
            value = Decimal(value)
        elif not isinstance(value, Decimal):
            value = Decimal(str(value))
        
        # Format with thousand separators
        return f"{value:,}"
        
    except (ValueError, TypeError):
        return str(value)

@register.simple_tag
def currency_symbol():
    """Return the currency symbol"""
    return settings.CURRENCY_SYMBOL

@register.simple_tag
def currency_code():
    """Return the currency code"""
    return settings.CURRENCY_CODE

@register.simple_tag
def currency_name():
    """Return the currency name"""
    return settings.CURRENCY_NAME
