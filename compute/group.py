#coding=utf-8

###############################################
# name: compute.group模块接口函数
# author: bobfu
# email: fubo@cnic.cn
# time: 2015-12-03
###############################################

from django.contrib.auth.models import User

from .models import Group as ModelGroup

    
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
    

