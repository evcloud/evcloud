#coding=utf-8
from .manager import CephManager, GfsManager
from api.error import Error
from api.error import ERR_CEPHPOOL_ID
from .models import CEPH_IMAGE_POOL_FLAG, CEPH_VOLUME_POOL_FLAG


def get_storage_api(backend):
    if backend == 'CEPH':
        return StorageAPI()
    elif backend == 'GFS':
        return StorageAPI(manager=GfsManager())
    return None


class StorageAPI(object):
    def __init__(self, manager=None):
        if manager:
            self.manager = manager
        else:
            self.manager = CephManager()
        super().__init__()
    
    def get_pool_list_by_center_id(self, center_id):
        return self.manager.get_pool_list_by_center_id(center_id)

    def get_pool_by_id(self, pool_id):
        return self.manager.get_pool_by_id(pool_id)

    def get_volume_pool_by_center_id(self, center_id):
        return self.manager.get_volume_pool_by_center_id(center_id)

    def clone(self, pool_id, src, dst):
        pool = self.get_pool_by_id(pool_id)
        return pool.clone(src, dst)

    def mv(self, pool_id, src, dst):
        pool = self.get_pool_by_id(pool_id)
        return pool.mv(src, dst)

    def rm(self, pool_id, dst):
        pool = self.get_pool_by_id(pool_id)
        return pool.rm(dst)

    def exists(self, pool_id, name):
        pool = self.get_pool_by_id(pool_id)
        return pool.exists(name)
    
    def create(self, pool_id, name, size):
        pool = self.get_pool_by_id(pool_id)
        return pool.create(name, size)

    def resize(self, pool_id, name, size):
        pool = self.get_pool_by_id(pool_id)
        return pool.resize(name, size)

    def create_snap(self, pool_id, name):
        if not self._valid_snap_name(name):
            return False
        pool = self.get_pool_by_id(pool_id)
        return pool.create_snap(name)

    def protect_snap(self, pool_id, name):
        if not self._valid_snap_name(name):
            return False
        pool = self.get_pool_by_id(pool_id)
        return pool.protect_snap(name)

    def rollback_snap(self, pool_id, name):
        if not self._valid_snap_name(name):
            return False
        pool = self.get_pool_by_id(pool_id)
        return pool.rollback_snap(name)

    def snap_exist(self,pool_id,name):
        if not self._valid_snap_name(name):
            return False
        pool = self.get_pool_by_id(pool_id)
        return pool.snap_exist(name)

    def rm_snap(self,pool_id,name):
        if not self._valid_snap_name(name):
            return False
        pool = self.get_pool_by_id(pool_id)
        if not pool.snap_exist(name):
            return True
        return pool.rm_snap(name)

    def _valid_snap_name(self, snap_name):
        try:
            names = snap_name.split("@")
            if len(names)==2 and len(names[0].strip())>0 and len(names[1].strip())>0 :
                return True
            else:
                return False
        except:
            return False