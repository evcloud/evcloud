#coding=utf-8

from .models import Vlan as ModelVlan
 
class Vlan(object):
    def __init__(self, obj):
        self.db_obj = obj        
        if type(obj) == ModelVlan:
            self.db_obj = obj
        else:
            raise RuntimeError('Vlan init error.')

        self.id = self.db_obj.id
        self.vlan = self.db_obj.vlan
        self.br = self.db_obj.br
        self.type_code = self.db_obj.type.code
        self.type_name = self.db_obj.type.name
        self.enable = self.db_obj.enable
        self.remarks = self.db_obj.remarks
        self.order = self.db_obj.order

    @property
    def ip_count(self):
        return self.db_obj.macip_set.all().count()
    
    @property
    def ip_used(self):
        return self.db_obj.macip_set.exclude(vmid='').exclude(vmid__isnull=True).count()
        
    def has_free_ip(self, num=1):
        return self.ip_used + num <= self.ip_count

    def managed_by(self, user):
        if user.is_superuser:
            return True
        return self.db_obj.host_set.filter(group__admin_user = user).exists()