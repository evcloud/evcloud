#coding=utf-8

###############################################
# name: compute.center模块接口函数
# author: bobfu
# email: fubo@cnic.cn
# time: 2015-12-03
###############################################
from .models import Center as ModelCenter


class Center(object):
    def __init__(self, obj):
        self.db_obj = obj        
        if type(obj) == ModelCenter:
            self.db_obj = obj
        else:
            raise RuntimeError('Center init error.')
        
    def __getattr__(self, name):
        return self.db_obj.__getattribute__(name)
    
    def managed_by(self, user):
        if user.is_superuser:
            return True
        from .api import GroupAPI
        return GroupAPI().has_center_perm(user, self.db_obj.id)