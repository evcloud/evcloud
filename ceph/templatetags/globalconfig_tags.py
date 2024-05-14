from django import template
from django.core.cache import cache
from ceph.models import GlobalConfig

register = template.Library()


@register.simple_tag
def get_global_config_tag():

    global_config_obj = GlobalConfig().get_instance()
    if not global_config_obj:
        return None

    return global_config_obj