#coding=utf-8
from django.db import models

app_label = 'monitoring'

class HostErrorLog(models.Model):
    host_id = models.IntegerField()
    host_ipv4 = models.GenericIPAddressField()
    info = models.TextField(default='', null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        app_label = app_label
        verbose_name = '宿主机故障记录'
        verbose_name_plural = '1_宿主机故障记录'


class VmMigrateLog(models.Model):
    host_error_log_id = models.IntegerField(null=True,help_text="引起虚拟机迁移的宿主机故障记录")
    vm_uuid = models.CharField(max_length=100, unique=True)
    vm_ipv4 = models.GenericIPAddressField() 
    src_host_ipv4 = models.GenericIPAddressField()
    dst_host_ipv4 = models.GenericIPAddressField()
    migrate_res = models.BooleanField(default=False)    
    info = models.TextField(default='', null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        app_label = app_label
        verbose_name = '高可用虚拟机迁移记录'
        verbose_name_plural = '2_高可用虚拟机迁移记录'

