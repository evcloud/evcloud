#coding=utf-8

###############################################
# name: compute.group模块接口函数
# author: bobfu
# email: fubo@cnic.cn
# time: 2015-12-03
###############################################

from django.contrib.auth.models import User

from .models import Group as ModelGroup

#即将删除
def get_groups_in_perm(user, center_id = None):
    if user.is_superuser:
        if center_id == None:
            groups = ModelGroup.objects.all()
        else:
            groups = ModelGroup.objects.filter(center_id = center_id)
    else:
        if center_id == None:
            groups = ModelGroup.objects.filter(admin_user = user)
        else:
            groups = ModelGroup.objects.filter(admin_user = user, center_id = center_id)
    groups = groups.order_by('order')
    ret_list = []
    for group in groups:
        ret_list.append(_get_group_data(group))
    return ret_list

#即将删除
def get_group(group_id):
    group = ModelGroup.objects.filter(id = group_id)
    if not group.exists():
        return False
    return _get_group_data(group[0])

#即将删除
def has_center_perm(user, center_id):
    '''对指定center有部分或全部管理权，即对该分中心中的 某个集群有管理权,则返回True'''
    return ModelGroup.objects.filter(admin_user = user, center_id = center_id).exists()




#--------------------------------------------------------
#即将删除
def _get_group_data(group):
    if not type(group) == ModelGroup:
        return False
    return Group(group)
    
    
class Group(object):
    def __init__(self, obj):      
        if type(obj) == ModelGroup:
            self.db_obj = obj
        else:
            raise RuntimeError('Group init error.')
        
        self.id = self.db_obj.id
        self.center_id = self.db_obj.center_id 
        self.name = self.db_obj.name
        self.desc = self.db_obj.desc
        self.admin_user = [user for user in self.db_obj.admin_user.all()]
        self.order = self.db_obj.order
        
    
    def managed_by(self, user):
        if user.is_superuser:
            return True
        return user in self.db_obj.admin_user.all()
    

