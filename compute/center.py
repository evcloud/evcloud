#coding=utf-8

###############################################
# name: compute.center模块接口函数
# author: bobfu
# email: fubo@cnic.cn
# time: 2015-12-03
###############################################

from django.contrib.auth.models import User

from .group import has_center_perm
from .models import Center as ModelCenter


def get_center(center_id):
    center = ModelCenter.objects.filter(id = center_id)
    if not center.exists():
        return False
    center = center[0]
    return _get_center_data(center)

def get_centers():
    centers = ModelCenter.objects.all()
    ret_list = []
    for center in centers:
        ret_list.append(_get_center_data(center))
    return ret_list

def _get_center_data(center):
    if type(center) != ModelCenter:
        return False
    return Center(center)

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
        return has_center_perm(user, self.db_obj.id)