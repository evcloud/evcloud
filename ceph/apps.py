from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CephConfig(AppConfig):
    name = 'ceph'
    verbose_name = _('全局变量')
