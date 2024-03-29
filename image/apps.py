from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ImageConfig(AppConfig):
    name = 'image'
    verbose_name = _('系统镜像和模板')
