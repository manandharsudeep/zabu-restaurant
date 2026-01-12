from django.conf import settings

def currency_context(request):
    """Add currency settings to all templates"""
    return {
        'CURRENCY_SYMBOL': getattr(settings, 'CURRENCY_SYMBOL', 'Rs.'),
        'CURRENCY_CODE': getattr(settings, 'CURRENCY_CODE', 'NPR'),
        'CURRENCY_NAME': getattr(settings, 'CURRENCY_NAME', 'Nepalese Rupee'),
        'LOCALE_NAME': getattr(settings, 'LOCALE_NAME', 'ne_NP'),
    }
