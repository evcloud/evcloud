#coding=utf-8

from .models import CephPool as DBPool
from .models import CEPH_VOLUME_POOL_FLAG
from .ceph import CephPoolData
from .gfs import GfsPoolData
from api.error import Error
from api.error import ERR_CEPHPOOL_ID


class CephManager(object):
    
    def get_pool_list_by_center_id(self, center_id):
        pool_list = DBPool.objects.filter(host__center_id=center_id, enable=True)
        ret_list = []
        for pool in pool_list:
            p = self._get_ceph_data(pool)
            if p:
                ret_list.append(p)
        return ret_list

    def get_volume_pool_by_center_id(self, center_id):
        pool_list = DBPool.objects.filter(host__center_id=center_id, enable=True, type=CEPH_VOLUME_POOL_FLAG)
        if pool_list.exists():
            return self._get_ceph_data(pool_list[0])
        return None

    def get_pool_by_id(self, cephpool_id):
        cephpool = DBPool.objects.filter(id=cephpool_id)
        if not cephpool.exists():
            raise Error(ERR_CEPHPOOL_ID)
        return self._get_ceph_data(cephpool[0])

    def _get_ceph_data(self, pool):
        if not type(pool) == DBPool:
            return False
        
        p = CephPoolData(pool)
        
        return p


class GfsManager(object):
    def get_pool_list_by_center_id(self, center_id):
        pool_list = DBPool.objects.filter(center_id=center_id)
        ret_list = []
        for pool in pool_list:
            p = self._get_ceph_data(pool)
            if p:
                ret_list.append(p)
        return ret_list

    def get_volume_pool_by_center_id(self, center_id):
        pool_list = DBPool.objects.filter(host__center_id=center_id, enable=True, type=CEPH_VOLUME_POOL_FLAG)
        if pool_list.exists():
            return self._get_ceph_data(pool_list[0])
        return None

    def get_pool_by_id(self, cephpool_id):
        pool = DBPool.objects.filter(id=cephpool_id)
        if not pool.exists():
            raise Error(ERR_CEPHPOOL_ID)
        return self._get_ceph_data(pool[0])

    def _get_ceph_data(self, pool):
        if not type(pool) == DBPool:
            return False

        p = GfsPoolData(pool)

        return p