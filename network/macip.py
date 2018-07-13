#coding=utf-8

from .models import MacIP as ModelMacIp
 
class MacIp(object):
    def __init__(self, obj):
        self.db_obj = obj        
        if type(obj) == ModelMacIp:
            self.db_obj = obj
        else:
            raise RuntimeError('MacIp init error.')

        self.id = self.db_obj.id
        self.vlan = self.db_obj.vlan.vlan
        self.mac = self.db_obj.mac
        self.ipv4 = self.db_obj.ipv4
        self.vmid = self.db_obj.vmid
        self.enable = self.db_obj.enable