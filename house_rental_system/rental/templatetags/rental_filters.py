from django import template

register = template.Library()

@register.filter
def npr_currency(value):
    """Format number as Nepali currency with रू symbol"""
    try:
        amount = float(value)
        return f"रू {amount:,.2f}"
    except (ValueError, TypeError):
        return f"रू {value}"

@register.filter
def npr(value):
    """Shorter version - just add रू prefix"""
    try:
        return f"रू {float(value):,.2f}"
    except (ValueError, TypeError):
        return value