#coding=utf-8
from django.db import models
from compute.models import Host as DBHost


class DBGPU(models.Model):
    host = models.ForeignKey(DBHost)
    address = models.CharField(max_length=100, help_text='format:<domain>:<bus>:<slot>:<function>, example: 0000:84:00:0')
    vm = models.CharField(max_length=200, null=True, blank=True)
    attach_time = models.DateTimeField(null=True, blank=True)
    enable = models.BooleanField(default=True)
    remarks = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.host.ipv4 + '_' + self.address 

    class Meta:
        verbose_name = 'GPU'
        verbose_name_plural = 'GPU' 



