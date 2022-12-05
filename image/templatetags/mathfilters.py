from django import template
from django.utils import formats
from django.utils.html import avoid_wrapping
from django.utils.translation import ugettext, ungettext

register = template.Library()

@register.filter(is_safe=True)
def subtract(value, arg):
    return value - arg