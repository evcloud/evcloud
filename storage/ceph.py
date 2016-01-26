#coding=utf-8
#
# @author bobfu 
# @date 2015-09-17
# @desc 对ceph进行封装，提供 clone、mv、rm 、create四个基本函数
#
#

###############################################
# name: storage模块接口函数
# author: bobfu
# email: fubo@cnic.cn
# time: 2015-12-03
###############################################
import subprocess

from .models import CephPool as ModelCephPool

from compute.group import has_center_perm
from django.contrib.auth.models import User

#即将删除
def get_cephpools(center_id):
    pool_list = ModelCephPool.objects.filter(host__center_id = center_id)
    ret_list = []
    
    for pool in pool_list:
        p = _get_ceph_data(pool)
        if p:
            ret_list.append(p)

    return ret_list

#即将删除
def get_cephpool(cephpool_id):
    print(1)
    cephpool = ModelCephPool.objects.filter(id = cephpool_id)
    print(cephpool)
    if not cephpool.exists():
        return False
    return _get_ceph_data(cephpool[0])

#即将删除
def _get_ceph_data(pool):
    if not type(pool) == ModelCephPool:
        return False
    
    p = CephPoolData(pool)
    return p


class CephPool(object):
    
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
    
    def managed_by(self, user):
        if user.is_superuser:
            return True
        return has_center_perm(user, self.center_id)
       

