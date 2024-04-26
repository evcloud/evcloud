from django.db import models
from django.utils.translation import gettext_lazy as _


# Create your models here.


class LogRecord(models.Model):

    id = models.AutoField(primary_key=True, verbose_name=_('ID'))
    status_code = models.IntegerField(verbose_name=_('状态码'), blank=True, default=0)
    method = models.CharField(verbose_name=_('请求方法'), max_length=32, blank=True, default='')
    operation_content = models.CharField(verbose_name=_('操作内容'), max_length=255, default=None)  # 用户行为  --重建云主机
    full_path = models.CharField(verbose_name=_('请求路径'), max_length=1024, blank=True, default='')
    message = models.TextField(verbose_name=_('备注信息'), blank=True, default='')
    create_time = models.DateTimeField(verbose_name=_('创建时间'), auto_now_add=True)
    username = models.CharField(verbose_name=_('请求用户'), max_length=150, blank=True, default='')

    class Meta:
        verbose_name = _("用户操作日志")
        verbose_name_plural = verbose_name
        db_table = "log_record_user"
        ordering = ["-create_time"]
