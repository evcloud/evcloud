#coding=utf-8
from django.db import models

from compute.models import Center,Group,Host
# Create your models here.

####lzx###

class Alloc_Center(models.Model):
    center = models.ForeignKey(Center) 
    center_name = models.CharField(max_length = 100)
    vcpu_total = models.IntegerField(default = 0) 
    vcpu_allocated = models.IntegerField(default=0) 
    vcpu_alloc_rate = models.FloatField() 
    mem_total = models.IntegerField()
    mem_allocated = models.IntegerField(default=0)
    mem_reserved = models.IntegerField(default=2097152)
    mem_alloc_rate = models.FloatField()
    record_datetime = models.CharField(max_length=50)
    def __unicode__(self):
        return self.center_name
    
    class Meta:
        verbose_name = '报告_分中心'
        verbose_name_plural = verbose_name

class Alloc_Center_Latest(models.Model):
        center = models.ForeignKey(Center)
        center_name = models.CharField(max_length = 100)
        vcpu_total = models.IntegerField(default = 0)
        vcpu_allocated = models.IntegerField(default=0)
        vcpu_alloc_rate = models.FloatField()
        mem_total = models.IntegerField()
        mem_allocated = models.IntegerField(default=0)
        mem_reserved = models.IntegerField(default=2097152)
        mem_alloc_rate = models.FloatField()
        record_datetime = models.CharField(max_length=50)
        def __unicode__(self):
                return self.center_name

        class Meta:
                verbose_name = '报告_分中心'
                verbose_name_plural = verbose_name


class Alloc_Group(models.Model):
    group = models.ForeignKey(Group)
    group_name = models.CharField(max_length = 100)
    center= models.ForeignKey(Center) 
    vcpu_total = models.IntegerField()
    vcpu_allocated = models.IntegerField(default=0)
    vcpu_alloc_rate = models.FloatField() 
    mem_total = models.IntegerField()
    mem_allocated = models.IntegerField(default=0)
    mem_reserved = models.IntegerField(default=2097152)
    mem_alloc_rate = models.FloatField() 
    record_datetime = models.CharField(max_length=50)	
    def __unicode__(self):
        return self.group_name
    
    class Meta:
        verbose_name = '报告_主机组'
        verbose_name_plural = verbose_name

class Alloc_Group_Latest(models.Model):
        group = models.ForeignKey(Group)
        group_name = models.CharField(max_length = 100)
        center= models.ForeignKey(Center)
        vcpu_total = models.IntegerField()
        vcpu_allocated = models.IntegerField(default=0)
        vcpu_alloc_rate = models.FloatField()
        mem_total = models.IntegerField()
        mem_allocated = models.IntegerField(default=0)
        mem_reserved = models.IntegerField(default=2097152)
        mem_alloc_rate = models.FloatField()
        record_datetime = models.CharField(max_length=50)
        def __unicode__(self):
                return self.group_name

        class Meta:
                verbose_name = '报告_主机组'
                verbose_name_plural = verbose_name



class Alloc_Host(models.Model):
    host = models.ForeignKey(Host)
    group = models.ForeignKey(Group)
    ipv4  = models.GenericIPAddressField()
    vcpu_total = models.IntegerField()
    vcpu_allocated = models.IntegerField(default=0)
    vcpu_alloc_rate = models.FloatField() 
    mem_total = models.IntegerField()
    mem_allocated = models.IntegerField(default=0)
    mem_reserved = models.IntegerField(default=2097152)
    mem_alloc_rate = models.FloatField()
    record_datetime = models.CharField(max_length=50)
    def __unicode__(self):
        return self.ipv4
    
    class Meta:
        verbose_name = '报告_宿主机'
        verbose_name_plural = verbose_name
    

class Alloc_Host_Latest(models.Model):
    host  = models.ForeignKey(Host)
    group = models.ForeignKey(Group)
    ipv4  = models.GenericIPAddressField()
    vcpu_total = models.IntegerField()
    vcpu_allocated = models.IntegerField(default=0)
    vcpu_alloc_rate = models.FloatField()
    mem_total = models.IntegerField()
    mem_allocated = models.IntegerField(default=0)
    mem_reserved = models.IntegerField(default=2097152)
    mem_alloc_rate = models.FloatField()
    record_datetime = models.CharField(max_length=50)
    def __unicode__(self):
        return self.ipv4

    class Meta:
        verbose_name = '报告_宿主机'
        verbose_name_plural = verbose_name