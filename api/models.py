#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2015-10-16
#@desc:     API模块的model
########################################################################

from django.db import models
from django.contrib.auth.models import User
from compute.models import Group
from django.contrib.auth.admin import UserAdmin
    
class Log(models.Model):
    user = models.CharField(max_length=100)
    op = models.CharField(max_length=50)
    start_time = models.DateTimeField()
    finish_time = models.DateTimeField()
    result = models.BooleanField()
    error = models.TextField(null=True, blank=True)
    from_trd_part = models.BooleanField(default=False)
    args = models.TextField(null=True, blank=True)
    class Meta:
        verbose_name = 'API日志'
        verbose_name_plural = '2_API日志'
    

class ProfileBase(type):                    
    def __new__(cls,name,bases,attrs):      
        module = attrs.pop('__module__')
        parents = [b for b in bases if isinstance(b, ProfileBase)]  
        if parents:  
            fields = []  
            for obj_name, obj in attrs.items():  
                if isinstance(obj, models.Field): fields.append(obj_name)  
                User.add_to_class(obj_name, obj)  
            UserAdmin.fieldsets = list(UserAdmin.fieldsets)  
            UserAdmin.fieldsets.insert(1, (name, {'fields': fields}))  
            UserAdmin.list_display = tuple(list(UserAdmin.list_display) + fields)
            UserAdmin.list_display = tuple(list(UserAdmin.list_display) + ['is_superuser'])
        return super(ProfileBase, cls).__new__(cls, name, bases, attrs)  

class ProfileUser(object):  
    __metaclass__ = ProfileBase    
    
class MyProfile(ProfileUser):  
    api_user = models.BooleanField('API用户', default=False)
UserAdmin.list_filter = tuple(list(UserAdmin.list_filter) + ['api_user'])
