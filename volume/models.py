#coding=utf-8
from django.db import models
from django.contrib.auth.models import User
from storage.models import CephPool
from compute.models import Group

class AbsDBVolume(models.Model):
    '''附加磁盘抽象类'''
    class Meta:
        abstract = True
    
    uuid = models.CharField(max_length=200, primary_key=True)
    user = models.ForeignKey(User, null=True, blank=True)
    group = models.ForeignKey(Group, null=True, blank=True)
    creator = models.CharField(max_length=200, null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    size = models.IntegerField()
    remarks = models.TextField(null=True, blank=True)
    vm = models.CharField(max_length=200, null=True, blank=True)
    attach_time = models.DateTimeField(null=True, blank=True)
    dev = models.CharField(max_length=100, null=True, blank=True)
    enable = models.BooleanField(default=True)


class DBCephVolume(AbsDBVolume):
    '''ceph块'''
    cephpool = models.ForeignKey(CephPool)

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


class DBCephQuota(models.Model):
    '''
    计算集群在指定存储卷上可申请的存储容量限额，total集群总容量限额，volume对应单块云硬盘容量限额
    '''
    group = models.ForeignKey(Group, verbose_name='计算集群', null=True, blank=True,  
        help_text='')
    cephpool = models.ForeignKey(CephPool, verbose_name='存储卷', null=True, blank=True,  
        help_text='')
    total = models.IntegerField('集群总容量', help_text='单位MB')
    volume = models.IntegerField('云硬盘容量', help_text='单位MB')
    
    class Meta:
        verbose_name = 'Ceph云硬盘配额'
        verbose_name_plural = '2_Ceph云硬盘配额'
        unique_together = ('group', 'cephpool')
    
    def total_g(self):
        if self.total is None:
            return None
        return self.total / 1024
    total_g.short_description = '集群总容量(GB)'
    
    def volume_g(self):
        if self.volume is None:
            return None
        return self.volume / 1024
    volume_g.short_description = '云硬盘最大容量(GB)'


# VOLUME_OPERATION_CREATE = 0
# VOLUME_OPERATION_MOUNT  = 1
# VOLUME_OPERATION_UMOUNT = 2
# VOLUME_OPERATION_RESIZE = 3
# VOLUME_OPERATION_REMARK = 4
# VOLUME_OPERATION_DELETE = 5
# VOLUME_TYPE_CEPH = 0

# class DBVolumeLog(models.Model):
#     operate_type_list = (
#         (VOLUME_OPERATION_CREATE, '创建'),
#         (VOLUME_OPERATION_MOUNT,  '挂载'),
#         (VOLUME_OPERATION_UMOUNT, '卸载'),
#         (VOLUME_OPERATION_RESIZE, '修改容量'),
#         (VOLUME_OPERATION_REMARK, '修改备注'),
#         (VOLUME_OPERATION_DELETE, '删除'),
#         )
#     storage_type_list = (
#         (VOLUME_TYPE_CEPH, 'Ceph'),
#         )
#     operate_user = models.CharField(max_length=200)
#     operate_time = models.DateTimeField(auto_now_add=True)
#     operate_type = models.IntegerField(choices=operate_type_list)
#     vmid = models.CharField(max_length=200, null=True, blank=True)
#     volume_id = models.CharField(max_length=200)
#     volume_type = models.IntegerField(choices=storage_type_list)
#     # remarks = models.TextField(null=True, blank=True)
