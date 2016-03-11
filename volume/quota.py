#coding=utf-8

from .models import DBCephQuota
from .models import DBCephVolume
from django.db.models import Sum 

class CephQuota(object):
    def get_group_quota_by_group_id(self, group_id):
        q = DBCephQuota.objects.filter(group_id = group_id)
        if q.exists():
            return (q[0].total, q[0].volume)
        q = DBCephQuota.objects.filter(group_id=None)
        if q.exists():
            return (q[0].total, q[0].volume)
        return False

    def can_create(self, group_id, size):
        q = self.get_group_quota_by_group_id(group_id)
        if q:   
            if size > q[1]:
                return False
            if self.get_group_used_size(group_id) + size > q[0]:
                return False
        return True

    def group_quota_validate(self, group_id, size, old_size=0):
        q = self.get_group_quota_by_group_id(group_id)
        print(q)
        if q:   
            if self.get_group_used_size(group_id) - old_size + size > q[0]:
                return False
        return True

    def volume_quota_validate(self, group_id, size):
        q = self.get_group_quota_by_group_id(group_id)
        if q:   
            if size > q[1]:
                return False
        return True

    def get_group_used_size(self, group_id):
        total_size_sum = DBCephVolume.objects.filter(group_id = group_id).aggregate(Sum('size'))
        total = total_size_sum['size__sum']
        if not total:
            return 0
        return int(total)