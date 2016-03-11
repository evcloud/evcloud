#coding=utf-8
from django.contrib.auth.models import User

from api.error import (ERR_DISK_INIT, ERR_DISK_ARCHIVE, ERR_CEPH_ID,
                       ERR_IMAGE_INFO, ERR_IMAGE_CEPHHOST, ERR_IMAGE_CEPHPOOL) 
from api.error import Error


from .models import Image as DBImage
from .models import ImageType


class Image(object):
    def __init__(self, obj):
        self.db_obj = obj        
        if type(obj) == DBImage:
            self.db_obj = obj
        else:
            raise RuntimeError('Image init error.')
        
        self.xml = self.db_obj.xml.xml
        self.type_code = self.db_obj.type.code
        self.type_name = self.db_obj.type.name
        
    def __getattr__(self, name):
        return self.db_obj.__getattribute__(name)
    
    def managed_by(self, user):
        if type(user) != User:
            raise RuntimeError('user type error.')
        if user.is_superuser:
            return True
        from compute.api import GroupAPI
        return GroupAPI().has_center_perm(user, self.db_obj.cephpool.host.center.id)