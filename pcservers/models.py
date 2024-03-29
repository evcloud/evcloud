from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _  #  gettext 不生效


User = get_user_model()


class Department(models.Model):
    """
    部门
    """
    id = models.AutoField(primary_key=True, verbose_name=_('ID'))
    number = models.CharField(max_length=100, verbose_name=_('部门编号'))
    name = models.CharField(max_length=255, verbose_name=_('部门名称'))

    class Meta:
        ordering = ['id']
        verbose_name = _('部门')
        verbose_name_plural = _('部门')

    def __str__(self):
        return self.name


class Room(models.Model):
    """
    机房
    """
    id = models.AutoField(primary_key=True, verbose_name=_('ID'))
    name = models.CharField(max_length=255, verbose_name=_('机房名称'))
    city = models.CharField(max_length=255, verbose_name=_('所在城市'))
    desc = models.CharField(max_length=255, default='', blank=True, verbose_name=_('描述'))

    class Meta:
        ordering = ['id']
        verbose_name = _('机房')
        verbose_name_plural = _('机房')

    def __str__(self):
        return f'{self.city}-{self.name}'


class ServerType(models.Model):
    """
    服务器型号
    """
    id = models.AutoField(primary_key=True, verbose_name=_('ID'))
    name = models.CharField(max_length=255, verbose_name=_('型号'))
    desc = models.TextField(default='', blank=True, verbose_name=_('描述'))

    class Meta:
        ordering = ['id']
        verbose_name = _('服务器型号')
        verbose_name_plural = _('服务器型号')

    def __str__(self):
        return self.name


class PcServer(models.Model):
    """
    服务器
    """

    STATUS_USING = 1
    STATUS_BORROW = 2
    STATUS_INVENTORY_LOSS = 3
    STATUS_IDLE = 4
    STATUS_FAULT = 5
    STATUS_SCRAP = 6
    STATUS_OTHER = 7

    STATUS_CHOICES = (
        (STATUS_USING, _('使用中')),
        (STATUS_BORROW, _('外借')),
        (STATUS_INVENTORY_LOSS, _('盘亏')),
        (STATUS_IDLE, _('空闲')),
        (STATUS_FAULT, _('故障')),
        (STATUS_SCRAP, _('已报废')),
        (STATUS_OTHER, _('其他')),
    )

    id = models.AutoField(primary_key=True, verbose_name=_('ID'))
    room = models.ForeignKey(to=Room, related_name='pc_server', null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_('所在机房'))
    server_type = models.ForeignKey(to=ServerType, related_name='pc_server', null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_('型号'))
    status = models.SmallIntegerField(default=STATUS_USING, choices=STATUS_CHOICES, verbose_name=_('状态'))
    buy_time = models.DateTimeField(null=True, blank=True, verbose_name=_('购买时间'))
    start_time = models.DateTimeField(null=True, blank=True, verbose_name=_('启用时间'))
    due_time = models.DateTimeField(null=True, blank=True, verbose_name=_('到期时间'))
    tag_no = models.CharField(max_length=255, verbose_name=_('标签号/序列号'))
    location = models.CharField(max_length=255, verbose_name=_('所在位置'))
    real_cpu = models.IntegerField(default=20, verbose_name=_('真实物理CPU总数'))
    real_mem = models.IntegerField(default=30, verbose_name=_('真实物理内存大小(Gb)'))
    host_ipv4 = models.CharField(max_length=100, verbose_name=_('主机IPv4地址'))
    ipmi_ip = models.CharField(max_length=100, verbose_name=_('IPMI管理地址'))
    host_ipv6 = models.CharField(max_length=100, default='', blank=True, verbose_name=_('主机IPv6地址'))
    ipmi_ipv6 = models.CharField(max_length=100, default='', blank=True, verbose_name=_('IPMI管理ipv6地址'))
    user = models.CharField(max_length=100, verbose_name=_('使用人'))
    contact = models.ForeignKey(to=User, related_name='pc_server', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('联系人'))
    department = models.ForeignKey(to=Department, null=True, on_delete=models.SET_NULL, verbose_name=_('部门'))
    use_for = models.TextField(blank=True, default='', verbose_name=_('用途'))
    remarks = models.TextField(blank=True, default='', verbose_name=_('备注'))
    hardware_info = models.TextField(blank=True, default='', verbose_name=_('硬件配置信息'))

    class Meta:
        ordering = ['id']
        verbose_name = _('服务器')
        verbose_name_plural = _('服务器')

    def __str__(self):
        return self.host_ipv4
