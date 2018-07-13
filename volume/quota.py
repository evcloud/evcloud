#coding=utf-8

from .models import DBCephQuota
from .models import DBCephVolume
from django.db.models import Sum 

class CephQuota(object):
    # def get_group_quota_by_group_id(self, group_id):
    #     q = DBCephQuota.objects.filter(group_id = group_id)
    #     if q.exists():
    #         return (q[0].total, q[0].volume)
    #     q = DBCephQuota.objects.filter(group_id=None)
    #     if q.exists():
    #         return (q[0].total, q[0].volume)
    #     return False

    def get_quota_list_by_group_id(self,group_id):
        '''
        获取指定集群的存储容量配额
        by lzx:2018-06-22
        '''
        q = DBCephQuota.objects.filter(group_id = group_id)
        if q.exists():
            return [{'id':obj.id,
                     'group_id':obj.group_id,
                     'cephpool_id':obj.cephpool_id,
                     'total_g':obj.total_g,
                     'volume_g':obj.volume_g} for obj in q if obj.group_id and obj.cephpool_id]       
        return []

    # def can_create(self, group_id, size):
    #     q = self.get_group_quota_by_group_id(group_id)
    #     if q:   
    #         if size > q[1]:
    #             return False
    #         if self.get_group_used_size(group_id) + size > q[0]:
    #             return False
    #     return True

    # def group_quota_validate(self, group_id, size, old_size=0):
    #     q = self.get_group_quota_by_group_id(group_id)
    #     print(q)
    #     if q:   
    #         if self.get_group_used_size(group_id) - old_size + size > q[0]:
    #             return False
    #     return True

    def group_pool_quota_validate(self, group_id, cephpool_id, size, old_size=0):
        '''
        验证集群在指定存储卷上的容量是否超过限制
        by lzx:2018-06-21
        '''
        q = self._get_group_pool_quota(group_id,cephpool_id)
        print(q)
        if q:   
            if self.get_group_pool_used_size(group_id,cephpool_id) - old_size + size > q[0]:
                return False
        return True

    # def volume_quota_validate(self, group_id, size):
    #     q = self.get_group_quota_by_group_id(group_id)
    #     if q:   
    #         if size > q[1]:
    #             return False
    #     return True

    def volume_pool_quota_validate(self, group_id, cephpool_id, size):
        '''
        验证集群在指定存储卷上的单个云硬盘容量是否超过限制        
        by lzx:2018-06-21        
        '''
        q = self._get_group_pool_quota(group_id,cephpool_id)
        if q:   
            if size > q[1]:
                return False
        return True

    # def get_group_used_size(self, group_id):
    #     total_size_sum = DBCephVolume.objects.filter(group_id = group_id).aggregate(Sum('size'))
    #     total = total_size_sum['size__sum']
    #     if not total:
    #         return 0
    #     return int(total)

    def get_group_pool_used_size(self, group_id,cephpool_id):
        '''
        获取集群在指定存储卷上已经使用的存储容量
        by lzx:2018-06-21        
        '''
        total_size_sum = DBCephVolume.objects.filter(group_id = group_id,cephpool_id=cephpool_id).aggregate(Sum('size'))
        total = total_size_sum['size__sum']
        if not total:
            return 0
        return int(total)

    def _get_group_pool_quota(self, group_id, cephpool_id):
        '''
        获取集群在指定存储卷上的容量限制
        by lzx:2018-06-21
        '''
        q = DBCephQuota.objects.filter(group_id = group_id, cephpool_id = cephpool_id)
        if q.exists():
            return (q[0].total, q[0].volume)        
        return False