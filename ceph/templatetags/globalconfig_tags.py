from django import template
from django.core.cache import cache
from ceph.models import GlobalConfig

register = template.Library()


@register.simple_tag
def get_global_config():

    global_config = cache.get('global_config_key')
    if global_config:
        return global_config

    global_config_obj = GlobalConfig().get_instance()
    if not global_config_obj:
        return None

    return global_config_obj
    # return global_config_obj.get_global_config()