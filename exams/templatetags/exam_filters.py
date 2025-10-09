# FILE: exams/templatetags/exam_filters.py (Modification)

from django import template

register = template.Library()

@register.filter
def sub(value, arg):
    # (Your existing subtraction logic remains here)
    try:
        return float(value) - float(arg) 
    except (ValueError, TypeError):
        return 0

@register.filter
def times(value, arg):
    # (Your existing multiplication logic remains here)
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

# --- NEW FILTER: Fixes the Invalid filter: 'div' error ---
@register.filter
def div(value, arg):
    """
    Divides the value by the argument.
    Example: {{ total_score|div:max_score }}
    """
    try:
        # Avoid division by zero
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0