from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class NetworkConfig(AppConfig):
    name = 'network'
    verbose_name = _('网络，IP与MAC')
