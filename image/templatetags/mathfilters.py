from django import template


register = template.Library()

@register.filter(is_safe=True)
def subtract(value, arg):
    return value - arg