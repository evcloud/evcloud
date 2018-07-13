#coding=utf-8
#
# @author bobfu 
# @date 2015-09-17
# @desc 对ceph进行封装，提供 clone、mv、rm 、create四个基本函数
#
#

###############################################
# name: storage模块接口函数# author: bobfu# email: fubo@cnic.cn# time: 2015-12-03
###############################################
import subprocess

from .models import CephPool as ModelCephPool
from .models import CEPH_IMAGE_POOL_FLAG
from .models import CEPH_VOLUME_POOL_FLAG

from django.contrib.auth.models import User



class CephPool(object):
    CEPH_IMAGE_POOL_FLAG = CEPH_IMAGE_POOL_FLAG
    CEPH_VOLUME_POOL_FLAG = CEPH_VOLUME_POOL_FLAG
    
    def __init__(self, host, pool):
        self._ceph_host = host
        self._ceph_pool = pool
        self.error = ''

    
    def clone(self, src, dst):
        cmd = 'ssh %(ceph_host)s rbd clone %(ceph_pool)s/%(src)s %(ceph_pool)s/%(dst)s' % {
            'ceph_host':self._ceph_host, 
            'ceph_pool':self._ceph_pool,
            'src':src, 
            'dst':dst
        }
        # print(cmd)
        res, info = subprocess.getstatusoutput(cmd)
        if res == 0:
            return True
        self.error = info
        return False
        
    def mv(self, src, dst):
        cmd = 'ssh %(ceph_host)s rbd mv %(ceph_pool)s/%(src)s %(ceph_pool)s/%(dst)s' % {
            'ceph_host':self._ceph_host, 
            'ceph_pool':self._ceph_pool,
            'src':src, 
            'dst':dst
        }
        res, info = subprocess.getstatusoutput(cmd)
        if res == 0:
            return True
        self.error = info
        return False
    
    def rm(self, dst):
        cmd = 'ssh %(ceph_host)s rbd rm %(ceph_pool)s/%(dst)s' % {
            'ceph_host':self._ceph_host, 
            'ceph_pool':self._ceph_pool,
            'dst':dst
        }
        res, info = subprocess.getstatusoutput(cmd)
        if res == 0:
            return True
        self.error = info
        return False
    
    def exists(self, name):
        cmd = 'ssh %(ceph_host)s rbd ls %(ceph_pool)s | grep ^%(name)s$ | wc -l' % {
            'ceph_host':self._ceph_host, 
            'ceph_pool':self._ceph_pool,
            'name':name
        }
        res, lines = subprocess.getstatusoutput(cmd)
        if res == 0:
            try:
                l = int(lines)
                if l > 0:
                    return True
            except: pass
        return False

    def create_snap(self, name):
        cmd = 'ssh %(ceph_host)s rbd snap create %(ceph_pool)s/%(name)s' % {
            'ceph_host':self._ceph_host, 
            'ceph_pool':self._ceph_pool,
            'name':name
        }
        res, lines = subprocess.getstatusoutput(cmd)
        if res == 0:
            return True
        return False        
    
    def protect_snap(self, name):
        cmd = 'ssh %(ceph_host)s rbd snap protect %(ceph_pool)s/%(name)s' % {
            'ceph_host':self._ceph_host, 
            'ceph_pool':self._ceph_pool,
            'name':name
        }
        res, lines = subprocess.getstatusoutput(cmd)
        if res == 0:
            return True
        return False     

    def create(self, name, size):
        cmd = 'ssh %(ceph_host)s rbd create %(name)s --size %(size)d --pool %(ceph_pool)s' % {
            'ceph_host': self._ceph_host, 
            'ceph_pool': self._ceph_pool,
            'name': name,
            'size': size
        }
        res, lines = subprocess.getstatusoutput(cmd)
        if res == 0:
            return True
        return False   
    
    def resize(self, name, size):
        cmd = 'ssh %(ceph_host)s rbd resize %(name)s --size %(size)d --pool %(ceph_pool)s' % {
            'ceph_host': self._ceph_host, 
            'ceph_pool': self._ceph_pool,
            'name': name,
            'size': size
        }
        res, lines = subprocess.getstatusoutput(cmd)
        if res == 0:
            return True
        return False  

class CephPoolData(CephPool):
    def __init__(self, obj):
        self.db_obj = obj        
        if type(obj) == ModelCephPool:
            self.db_obj = obj
            super(CephPoolData, self).__init__(obj.host.host, obj.pool)
        else:
            raise RuntimeError('ceph init error.')
        
        self.id = self.db_obj.id 
        self.pool = self.db_obj.pool 
        self.type = self.db_obj.type 
        self.center_id = self.db_obj.host.center.id
        self.host = self.db_obj.host.host
        self.port = self.db_obj.host.port 
        self.uuid = self.db_obj.host.uuid
        self.username = self.db_obj.host.username
        self.enable = self.db_obj.enable
        self.remarks = self.db_obj.remarks
    
    def managed_by(self, user):
        if user.is_superuser:
            return True
        from compute.api import GroupAPI
        return GroupAPI().has_center_perm(user, self.center_id)
       

