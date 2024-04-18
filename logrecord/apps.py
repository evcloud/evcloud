from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _



class LogrecordConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'logrecord'
    verbose_name = _('用户操作日志')
