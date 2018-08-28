# coding=utf-8
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
# time: 2017-12-09
###############################################
import subprocess
import os
from django.utils import timezone

from .models import CephPool as ModelGfsPool
from .models import CEPH_IMAGE_POOL_FLAG
from .models import CEPH_VOLUME_POOL_FLAG

from django.contrib.auth.models import User


class GfsPool(object):
    CEPH_IMAGE_POOL_FLAG = CEPH_IMAGE_POOL_FLAG
    CEPH_VOLUME_POOL_FLAG = CEPH_VOLUME_POOL_FLAG

    def __init__(self, host, pool):
        self._host = host
        self._pool = pool
        self.error = ''

    def clone(self, src, dst):
        cmd = 'ssh %(host)s cp %(src)s %(dst)s' % {
            'host': self._host,
            'src': os.path.join(self._pool, src),
            'dst': os.path.join(self._pool, dst)
        }
        res, info = subprocess.getstatusoutput(cmd)
        if res == 0:
            return True
        self.error = info
        return False

    def mv(self, src, dst):
        cmd = 'ssh %(host)s mv %(src)s %(dst)s' % {
            'host': self._host,
            'src': os.path.join(self._pool, src),
            'dst': os.path.join(self._pool, dst)
        }
        res, info = subprocess.getstatusoutput(cmd)
        if res == 0:
            return True
        self.error = info
        return False

    def rm(self, dst):
        cmd = 'ssh %(host)s rm %(path)s' % {
            'host': self._host,
            'path': os.path.join(self._pool, dst)
        }
        res, info = subprocess.getstatusoutput(cmd)
        if res == 0:
            return True
        self.error = info
        return False

    def exists(self, name):
        cmd = 'ssh %(host)s ls %(pool)s | grep ^%(name)s$ | wc -l' % {
            'host': self._host,
            'pool': self._pool,
            'name': name
        }
        res, lines = subprocess.getstatusoutput(cmd)
        if res == 0:
            try:
                l = int(lines)
                if l > 0:
                    return True
            except:
                pass
        return False

    def create_snap(self, name):
        cmd = 'ssh %(host)s qemu-img snapshot -c %(snap_name)s %(path)s' % {
            'host': self._host,
            'path': os.path.join(self._pool, name),
            'snap_name': name + str(timezone.now().timestamp())
        }
        res, lines = subprocess.getstatusoutput(cmd)
        if res == 0:
            return True
        return False

    def protect_snap(self, name):
        return True

    def create(self, name, size):
        cmd = 'ssh %(host)s qemu-img create -f qcow2 -o size=%(size)dM %(path)s' % {
            'host': self._host,
            'path': os.path.join(self._pool, name),
            'size': size
        }
        res, lines = subprocess.getstatusoutput(cmd)
        if res == 0:
            return True
        return False

    def resize(self, name, size):
        cmd = 'ssh %(host)s resize %(path)s %(size)dM' % {
            'host': self._host,
            'path': os.path.join(self._pool, name),
            'size': size
        }
        res, lines = subprocess.getstatusoutput(cmd)
        if res == 0:
            return True
        return False


class GfsPoolData(GfsPool):
    def __init__(self, obj):
        self.db_obj = obj
        if type(obj) == ModelGfsPool:
            self.db_obj = obj
            super().__init__(obj.host.host, obj.pool)
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


