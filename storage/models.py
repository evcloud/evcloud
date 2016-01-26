#coding=utf-8
from django.db import models
from compute.models import Center

app_label = 'storage'

class CephHost(models.Model):
    center = models.ForeignKey(Center)
    host = models.GenericIPAddressField()
    port = models.IntegerField(default=6789)
    uuid = models.CharField(max_length=100)
    username = models.CharField(max_length=100, default='admin')
    

    def __str__(self):
        return self.host
    
    class Meta:
        app_label = app_label
        verbose_name = 'Ceph集群'
        verbose_name_plural = '1_Ceph集群'

class CephPool(models.Model):
    ceph_pool_type = (
    (1, 'Image Pool'),
    (2, 'Volume Pool'),
    )
    host= models.ForeignKey(CephHost)
    pool = models.CharField(max_length=100)
    type = models.IntegerField(choices = ceph_pool_type)
    
    def __str__(self):
        return self.host.host + '_' + self.pool    
    
    class Meta:
        app_label = app_label
        verbose_name = 'Ceph资源池'
        verbose_name_plural = '2_Ceph资源池'
        unique_together = ('host', 'pool')



