#coding=utf-8
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

class ProfileBase(type):                    
    def __new__(cls,name,bases,attrs):      
        module = attrs.pop('__module__')
        parents = [b for b in bases if isinstance(b, ProfileBase)]  
        if parents:  
            fields = []  
            for obj_name, obj in list(attrs.items()):  
                if isinstance(obj, models.Field): fields.append(obj_name)  
                User.add_to_class(obj_name, obj)  
            UserAdmin.fieldsets = list(UserAdmin.fieldsets)  
            UserAdmin.fieldsets.insert(1, (name, {'fields': fields}))  
            UserAdmin.list_display = tuple(list(UserAdmin.list_display) + fields)
            UserAdmin.list_display = tuple(list(UserAdmin.list_display) + ['is_superuser'])
        return super(ProfileBase, cls).__new__(cls, name, bases, attrs)  

class ProfileUser(object, metaclass=ProfileBase):  
    pass
    
class MyProfile(ProfileUser):  
    api_user = models.BooleanField('API用户', default=False)
UserAdmin.list_filter = tuple(list(UserAdmin.list_filter) + ['api_user'])