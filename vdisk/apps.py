from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class VdiskConfig(AppConfig):
    name = 'vdisk'
    verbose_name = _("云硬盘设置")
