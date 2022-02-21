from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag(name='use_register_user')
def do_use_register_user():
    return getattr(settings, 'USE_REGISTER_USER', False)
