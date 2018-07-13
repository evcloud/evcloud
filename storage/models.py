#coding=utf-8
from django.db import models
from compute.models import Center

app_label = 'storage'

CEPH_IMAGE_POOL_FLAG = 1
CEPH_VOLUME_POOL_FLAG = 2


class CephHost(models.Model):
    CEPH = 'ceph'
    GFS = 'gfs'
    LOCAL = 'local'

    center = models.ForeignKey(Center)
    host = models.GenericIPAddressField()
    port = models.IntegerField(default=6789)
    uuid = models.CharField(max_length=100)
    username = models.CharField(max_length=100, default='admin')
    backend = models.CharField(max_length=50, choices=((CEPH, "CEPH"), (GFS, "GFS"), (LOCAL, "LOCAL")), default=CEPH)

    def __str__(self):
        return self.host
    
    class Meta:
        app_label = app_label
        verbose_name = '存储集群'
        verbose_name_plural = '1_存储集群'


class CephPool(models.Model):
    ceph_pool_type = (
    (CEPH_IMAGE_POOL_FLAG, 'Image Pool'),
    (CEPH_VOLUME_POOL_FLAG, 'Volume Pool'),
    )
    host = models.ForeignKey(CephHost)
    pool = models.CharField(max_length=100)
    type = models.IntegerField(choices = ceph_pool_type)
    enable = models.BooleanField(default=True)
    remarks = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return self.host.host + '_' + self.pool    
    
    class Meta:
        app_label = app_label
        verbose_name = '存储卷'
        verbose_name_plural = '2_存储卷'
        unique_together = ('host', 'pool')


