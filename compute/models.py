#coding=utf-8
from django.db import models
from django.contrib.auth.models import User

from network.models import Vlan

VM_NAME_LEN_LIMIT = 200

    
class Center(models.Model):
    name     = models.CharField('名称', max_length = 100, unique = True)
    location = models.CharField('位置', max_length = 100)
    desc     = models.CharField('简介', max_length = 200, null = True, blank = True)
    order    = models.IntegerField('排序', default=0, 
        help_text="用于在页面中的显示顺序，数值越小越靠前。")

    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name = '分中心'
        verbose_name_plural = '1_分中心'

class Group(models.Model):
    center = models.ForeignKey(Center)
    name   = models.CharField(max_length = 100)
    desc   = models.CharField(max_length = 200, null = True, blank = True)
    admin_user = models.ManyToManyField(User, blank = True)
    order    = models.IntegerField('排序', default=0, 
        help_text="用于在页面中的显示顺序，数值越小越靠前。")

    def __unicode__(self):
        return self.name   
#     
    class Meta:
        verbose_name = '集群'
        verbose_name_plural = '2_集群' 

class Host(models.Model):
    group = models.ForeignKey(Group)
    vlan  = models.ManyToManyField(Vlan)
    ipv4  = models.GenericIPAddressField(unique = True)
    vcpu_total       = models.IntegerField(default=24)
    vcpu_allocated   = models.IntegerField(default=0)
    mem_total       = models.IntegerField(default=32768)
    mem_allocated   = models.IntegerField(default=0)
    mem_reserved    = models.IntegerField(default=2038) 
    vm_limit        = models.IntegerField(default=10)
    vm_created      = models.IntegerField(default=0)
    enable          = models.BooleanField(default=True)
    desc   = models.CharField(max_length = 200, null = True, blank = True)
    
    def __unicode__(self):
        return self.ipv4

    class Meta:
        verbose_name = '宿主机'
        verbose_name_plural = '3_宿主机'

class Vm(models.Model):
    host        = models.ForeignKey(Host)
    image_id    = models.IntegerField(null=True, blank=True)
    image_snap  = models.CharField(max_length=200)
    image  = models.CharField(max_length=100)
    uuid        = models.CharField(max_length=100, unique=True)
    name        = models.CharField(max_length=VM_NAME_LEN_LIMIT)
    vcpu        = models.IntegerField()
    mem         = models.IntegerField()
    disk        = models.CharField(max_length=100)
    deleted     = models.BooleanField()
    creator     = models.CharField(max_length=200, null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    
    remarks = models.TextField(default='')
    
    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = '虚拟机'
        verbose_name_plural = '4_虚拟机'

class VmArchive(models.Model):
    center_id   = models.IntegerField(null=True, blank=True)
    center_name = models.CharField(max_length=100, null=True, blank=True)
    group_id    = models.IntegerField(null=True, blank=True)
    group_name  = models.CharField(max_length=100, null=True, blank=True)
    host_id     = models.IntegerField(null=True, blank=True)
    host_ipv4   = models.GenericIPAddressField(null=True, blank=True)
    ceph_host   = models.GenericIPAddressField(null=True, blank=True)
    ceph_pool   = models.CharField(max_length=100, null=True, blank=True)
    image_id    = models.IntegerField(null=True, blank=True)
    image_snap  = models.CharField(max_length=200, null=True, blank=True)
    name    = models.CharField(max_length=VM_NAME_LEN_LIMIT, null=True, blank=True)
    uuid    = models.CharField(max_length=100, null=True, blank=True)
    vcpu    = models.IntegerField(null=True, blank=True)
    mem     = models.IntegerField(null=True, blank=True)
    disk    = models.CharField(max_length=100, null=True, blank=True)
    mac     = models.CharField(max_length=17, null=True, blank=True)
    ipv4    = models.GenericIPAddressField(null=True, blank=True)
    vlan    = models.GenericIPAddressField(null=True, blank=True)
    br      = models.CharField(max_length=50, null=True, blank=True)

    remarks = models.TextField(default='')
    
    archive_time = models.DateTimeField(auto_now_add=True)
    
    creator     = models.CharField(max_length=200, null=True, blank=True)
    create_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = '虚拟机归档记录'
        verbose_name_plural = '5_虚拟机归档表'

class MigrateLog(models.Model):
    vmid = models.CharField(max_length=100)
    src_host_ipv4 = models.GenericIPAddressField()
    dst_host_ipv4 = models.GenericIPAddressField()
    migrate_time = models.DateTimeField(auto_now_add=True)
    result = models.BooleanField()
    error = models.TextField(null=True, blank=True)