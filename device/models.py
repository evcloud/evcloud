#coding=utf-8
from django.db import models
from compute.models import Host as DBHost
from vms.models import Vm as DBVm

class DeviceType(models.Model):
    '''
    PCIe设备类型
    '''
    id = models.AutoField(primary_key=True)
    name = models.CharField('类型名称', max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'PCIe设备'
        verbose_name_plural = '02_PCIe设备类型'

class Device(models.Model):
    '''
    PCIe设备
    '''
    id = models.AutoField(primary_key=True)
    type = models.ForeignKey(to=DeviceType, on_delete=models.CASCADE, verbose_name='类型')
    host = models.ForeignKey(DBHost, on_delete=models.CASCADE)
    address = models.CharField(max_length=100, help_text='format:<domain>:<bus>:<slot>:<function>, example: 0000:84:00:0')
    vm = models.ForeignKey(DBVm, null=True, blank=True, on_delete=models.CASCADE)
    attach_time = models.DateTimeField(null=True, blank=True)
    enable = models.BooleanField(default=True)
    remarks = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.host.ipv4 + '_' + self.address 

    class Meta:
        verbose_name = 'PCIe设备' 
        verbose_name_plural = '01_PCIe设备'