from django.db import models
from django.utils.translation import gettext_lazy as _


# Create your models here.


class LogRecord(models.Model):
    ADDITION = 1
    CHANGE = 2
    DELETION = 3
    SELECT = 4
    REBUILD = 5
    MIGRATE = 9
    SHELVE = 10
    UNSHELVE = 11
    VMS = 6
    VPN = 7
    VMDISK = 8
    DATACENTER = 12
    HOST = 13
    VLAN = 14
    IMAGE = 15
    USER = 16
    MOUNT = 17
    UNMOUNT = 18
    ASSETS = 19

    ACTION_FLAG_CHOICES = [
        (ADDITION, _("添加")),
        (CHANGE, _("修改")),
        (DELETION, _("删除")),
        (SELECT, _("查询")),
        (REBUILD, _("重建")),
        (MIGRATE, _("迁移")),
        (SHELVE, _("搁置")),
        (UNSHELVE, _("恢复搁置")),
        (MOUNT, _("挂载")),
        (UNMOUNT, _("卸载")),
    ]  # 操作类型

    TYPE = [
        (VMS, _("云主机")),
        (VPN, _("VPN")),
        (VMDISK, _("云硬盘")),
        (DATACENTER, _("数据中心")),
        (HOST, _("宿主机")),
        (VLAN, _("Vlan")),
        (IMAGE, _("镜像")),
        (USER, _("用户")),
        (ASSETS, _("资源统计")),
    ]

    id = models.AutoField(primary_key=True, verbose_name=_('ID'))
    status_code = models.IntegerField(verbose_name=_('状态码'), blank=True, default=0)
    method = models.CharField(verbose_name=_('请求方法'), max_length=32, blank=True, default='')
    action_flag = models.PositiveSmallIntegerField(verbose_name=_('操作'), choices=ACTION_FLAG_CHOICES, default=None)
    operation_content = models.CharField(verbose_name=_('操作内容'), max_length=255, default=None)  # 用户行为  --重建云主机
    resourc_type = models.PositiveSmallIntegerField(verbose_name=_('资源类型'), choices=TYPE,
                                                    default=None)  # 资源类型
    full_path = models.CharField(verbose_name=_('请求路径'), max_length=1024, blank=True, default='')
    message = models.TextField(verbose_name=_('日志信息'), blank=True, default='')
    create_time = models.DateTimeField(verbose_name=_('创建时间'), auto_now_add=True)
    username = models.CharField(verbose_name=_('请求用户'), max_length=150, blank=True, default='')

    class Meta:
        verbose_name = _("用户操作日志")
        verbose_name_plural = verbose_name
        db_table = "log_record_user"
        ordering = ["-create_time"]
