from django import template
from django.utils import formats
from django.utils.html import avoid_wrapping
from django.utils.translation import ugettext, ungettext

register = template.Library()

KB = 1 << 10
MB = 1 << 20
GB = 1 << 30
TB = 1 << 40
PB = 1 << 50


@register.filter(is_safe=True)
def sizeformat(value, arg="B"):
    """
    Formats the value like a 'human-readable' file size (i.e. 13 KB, 4.1 MB,
    102 byte_len, etc).
    """
    try:
        byte_len = float(value)
    except (TypeError, ValueError, UnicodeDecodeError):
        value = ungettext("%(size)d byte", "%(size)d byte_len", 0) % {'size': 0}
        return avoid_wrapping(value)

    def filesize_number_format(val):
        return formats.number_format(round(val, 1), 1)

    # 在原函数的基础上，添加了单位参数，使不同量级数据都可以被格式化
    switch = {
        'KB': KB,
        'MB': MB,
        'GB': GB,
        'TB': TB,
        'PB': PB
    }
    if arg in switch:
        byte_len *= switch[arg]

    if byte_len < KB:
        value = ungettext("%(size)d byte", "%(size)d byte_len", byte_len) % {'size': byte_len}
    elif byte_len < MB:
        value = ugettext("%s KB") % filesize_number_format(byte_len / KB)
    elif byte_len < GB:
        value = ugettext("%s MB") % filesize_number_format(byte_len / MB)
    elif byte_len < TB:
        value = ugettext("%s GB") % filesize_number_format(byte_len / GB)
    elif byte_len < PB:
        value = ugettext("%s TB") % filesize_number_format(byte_len / TB)
    else:
        value = ugettext("%s PB") % filesize_number_format(byte_len / PB)

    return avoid_wrapping(value)
