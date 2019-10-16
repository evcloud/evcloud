#coding=utf-8
from django.db import models
from django.contrib.auth.models import User
from ceph.models import CephPool
from compute.models import Group

class Vdisk(models.Model):
    '''附加磁盘类'''
    uuid = models.CharField(max_length=200, primary_key=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.CASCADE)
    creator = models.CharField(max_length=200, null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    size = models.IntegerField()
    remarks = models.TextField(null=True, blank=True)
    vm = models.CharField(max_length=200, null=True, blank=True)
    attach_time = models.DateTimeField(null=True, blank=True)
    dev = models.CharField(max_length=100, null=True, blank=True)
    enable = models.BooleanField(default=True)
    cephpool = models.ForeignKey(CephPool, on_delete=models.CASCADE)

    def __str__(self):
        return 'ceph_disk_' + str(self.uuid)
    
    class Meta:
        verbose_name = 'Ceph云硬盘'
        verbose_name_plural = '1_Ceph云硬盘'

    def size_g(self):
        if self.size is None:
            return None
        return self.size / 1024
    size_g.short_description = '容量(GB)'



class Quota(models.Model):
    '''
    计算集群在指定存储卷上可申请的存储容量限额，total集群总容量限额，vdisk对应单块云硬盘容量限额
    '''
    group = models.ForeignKey(Group, verbose_name='计算集群', null=True, blank=True,  
        help_text='', on_delete=models.CASCADE)
    cephpool = models.ForeignKey(CephPool, verbose_name='存储卷', null=True, blank=True,  
        help_text='', on_delete=models.CASCADE)
    total = models.IntegerField('集群总容量', help_text='单位MB')
    vdisk = models.IntegerField('云硬盘容量', help_text='单位MB')
    
    class Meta:
        verbose_name = 'Ceph云硬盘配额'
        verbose_name_plural = '2_Ceph云硬盘配额'
        unique_together = ('group', 'cephpool')
    
    def total_g(self):
        if self.total is None:
            return None
        return self.total / 1024
    total_g.short_description = '集群总容量(GB)'
    
    def vdisk_g(self):
        if self.vdisk is None:
            return None
        return self.vdisk / 1024
    vdisk_g.short_description = '云硬盘最大容量(GB)'