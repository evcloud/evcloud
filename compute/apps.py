from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ComputeConfig(AppConfig):
    name = 'compute'
    verbose_name = _('计算资源管理')
