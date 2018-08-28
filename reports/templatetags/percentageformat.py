#coding=utf-8

from django import template
from django.utils import formats
from django.utils.html import avoid_wrapping
from django.utils.translation import ugettext, ungettext

register = template.Library()

@register.filter(is_safe=True)
def percentageformat(value):
    """
    Formats the float value to percentage like  14.02%  22.19% etc).
    """
    p = ''
    try:
        value = float(value)
    except (TypeError, ValueError, UnicodeDecodeError):
        return avoid_wrapping(value)
    
    p = '%.2f%%' %(value*100)
    return avoid_wrapping(p)
