from django.core.cache import cache as dj_cache
from rest_framework.permissions import BasePermission

from ceph.models import ApiAllowIP

from utils.iprestrict import IPRestrictor, convert_iprange


class APIIPRestrictor(IPRestrictor):
    def __init__(self):
        self.reload_ip_rules()

    def reload_ip_rules(self):
        self.allowed_ips = self.get_allow_ipranges()

    @staticmethod
    def get_allow_ipranges():
        cache_key = 'nginx_api_allow_ips_cache'
        allow_ips = dj_cache.get(cache_key)
        if allow_ips is None:
            allow_ips = ApiAllowIP.objects.values_list('ip_value', flat=True)
            allow_ips = list(allow_ips)
            dj_cache.set(cache_key, allow_ips, timeout=60)

        allowed_ips = []
        for ip_str in allow_ips:
            try:
                allowed_ips.append(convert_iprange(ip_str))
            except Exception:
                pass

        return allowed_ips

    @staticmethod
    def clear_cache():
        dj_cache.delete('nginx_api_allow_ips_cache')


class APIIPPermission(BasePermission):
    """
    Allow ip
    """

    def has_permission(self, request, view):
        APIIPRestrictor().check_restricted(request=request)
        return True
