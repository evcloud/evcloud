#coding=utf-8

from .models import CephPool as DBCephPool
from .ceph import CephPoolData

def get_cephpool_list_by_center_id(center_id):
    pool_list = DBCephPool.objects.filter(host__center_id = center_id)
    ret_list = []
    
    for pool in pool_list:
        p = _get_ceph_data(pool)
        if p:
            ret_list.append(p)

    return ret_list

def get_cephpool(cephpool_id):
    cephpool = DBCephPool.objects.filter(id = cephpool_id)
    if not cephpool.exists():
        return False
    return _get_ceph_data(cephpool[0])

def _get_ceph_data(pool):
    if not type(pool) == DBCephPool:
        return False
    
    p = CephPoolData(pool)
    
    return p