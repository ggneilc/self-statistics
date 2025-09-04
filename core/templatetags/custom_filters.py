from django import template

register = template.Library()

@register.filter
def smart_num(value):
    try:
        return int(value) if value == int(value) else f"{value:.2f}"
    except (ValueError, TypeError):
        return value

@register.filter
def blank_check(value):
    return '?' if value is None else value
    