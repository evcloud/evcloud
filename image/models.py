#coding=utf-8
from django.db import models
from storage.models import CephPool

app_label = 'image'

class Xml(models.Model):
    name = models.CharField(max_length=100, unique=True)
    xml  = models.TextField()
    desc = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.name 

    class Meta:
        app_label = app_label
        verbose_name = '虚拟机XML模板'
        verbose_name_plural = '3_虚拟机XML模板'

class ImageType(models.Model):
    code = models.CharField('类型编号', max_length=50, primary_key = True)
    name = models.CharField('类型名称', max_length=100, unique = True)
    up_type = models.ForeignKey('self', null=True, blank=True)
    
    def __unicode__(self):
        return self.name 

    class Meta:
        app_label = app_label
        verbose_name = '镜像类型'
        verbose_name_plural = '2_镜像类型'
      
class Image(models.Model):
    cephpool    = models.ForeignKey(CephPool)
    name    = models.CharField(max_length=100)
    version = models.CharField(max_length=100)
    snap    = models.CharField(max_length=200)
    desc    = models.TextField()
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now = True)
    enable  = models.BooleanField(default=True)
    xml     = models.ForeignKey(Xml)
    type    = models.ForeignKey(ImageType)

    def __unicode__(self):
        return self.snap

    class Meta:
        app_label = app_label
        verbose_name = '镜像'
        verbose_name_plural = '1_镜像'
        unique_together = ('cephpool', 'name', 'version')

    @property
    def fullname(self):
        return self.name + ' ' + self.version

    
    



