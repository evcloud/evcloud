from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DeviceConfig(AppConfig):
    name = 'device'
    verbose_name = _("本地资源(GPU等PCIe设备)")
