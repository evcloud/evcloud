#coding=utf-8

from api.error import Error


from .models import DiskSnap as DBDiskSnap


class DiskSnap(object):
    def __init__(self, obj):
        self.db_obj = obj        
        if type(obj) == DBDiskSnap:
            self.db_obj = obj
        else:
            raise RuntimeError('DiskSnap init error.')
        

    def __getattr__(self, name):
        return self.db_obj.__getattribute__(name)

    def set_remarks(self,remarks):
        try:
            self.db_obj.remarks = remarks
            self.db_obj.save(update_fields=['remarks'])
        except Exception as e:
            return False
        return True
   