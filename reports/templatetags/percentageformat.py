from django import template
from django.utils.html import avoid_wrapping


register = template.Library()


@register.filter(is_safe=True)
def percentageformat(value, base):
    """
    Formats the result of divide value by base to percentage like  14.02%  22.19% etc).
    """
    if isinstance(value, int) and value == 0:
        return avoid_wrapping('0.00%')

    if value is None or not base:
        return avoid_wrapping(f'{value}/{base}')

    try:
        p = f'{(value / base)*100 :.2f}%'
    except Exception:
        return avoid_wrapping(f'{value}/{base}')

    return avoid_wrapping(p)
