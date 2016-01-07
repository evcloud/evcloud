#coding=utf-8
import commands
from django.db import transaction
from ..models import Host as ModelHost
from django.conf import settings

class Host(object):
    error = ''
    def __init__(self, db_obj):
        if type(db_obj) == ModelHost:
            self.db_obj = db_obj
        else:
            raise RuntimeError('Host init error.')
        self.upadte_data(db_obj)
        
    def upadte_data(self, db_obj):
        self.id = db_obj.id 
        self.center_id = db_obj.group.center_id
        self.group_id = db_obj.group_id
        self.ipv4 = db_obj.ipv4 
        self.vcpu_total = db_obj.vcpu_total
        self.vcpu_allocated = db_obj.vcpu_allocated
        self.mem_total = db_obj.mem_total
        self.mem_allocated = db_obj.mem_allocated
        self.mem_reserved = db_obj.mem_reserved
        self.vm_limit = db_obj.vm_limit
        self.vm_created = db_obj.vm_created
        self.enable = db_obj.enable
        self.desc = db_obj.desc
        
        self.vlans = [vlan.vlan for vlan in db_obj.vlan.all()]
        self.vlan_types = [(vlan.type.code, vlan.type.name) for vlan in db_obj.vlan.all()]
        
#     def __getattr__(self, name):
#         return self.db_obj.__getattribute__(name)
    
    def alive(self, times=3):
        # cmd = 'ping %s -c %d' % (self.db_obj.ipv4, times)
        cmd = 'fping %s -r %d' % (self.db_obj.ipv4, times)
        res, info = commands.getstatusoutput(cmd)
        if res == 0:
            return True
        return False
            
    def claim(self, vcpu, mem, vm_num = 1, fake=False):
        if settings.DEBUG:print 'claim resource', vcpu, mem
        if type(vcpu) != int or type(mem) != int or type(vm_num) != int:
            try:
                vcpu = int(vcpu)
                mem = int(mem)
                vm_num = int(vm_num)
            except:
                if settings.DEBUG: print 'host claim args error.'     
                self.error = 'args error.'
                return False
        
        if vcpu < 0 or mem < 0 or vm_num < 0:
            if settings.DEBUG: print 'host claim args < 0'  
            self.error = 'args error.'
            return False

        with transaction.atomic():
#             if self.db_obj.vcpu_allocated + vcpu > self.db_obj.vcpu_total:
#                 self.error = 'vcpu not enough.'
#                 return False
            if self.db_obj.mem_allocated + self.db_obj.mem_reserved + mem > self.db_obj.mem_total:
                self.error = 'mem not enough.'
                return False 
            if self.db_obj.vm_created + vm_num > self.db_obj.vm_limit:
                self.error = 'exceed vm limit.'
                return False
            
            if fake == True:
                return True
            try:
                self.db_obj.vcpu_allocated += vcpu
                self.db_obj.mem_allocated += mem
                self.db_obj.vm_created += vm_num
                self.db_obj.save()
            except Exception,e:
                if settings.DEBUG: print 'host claim.', e.message  
                self.error = e.message
                return False
            return True

    def release(self, vcpu, mem, vm_num = 1, fake=False):
        if settings.DEBUG: print 'release resource', vcpu, mem
        if type(vcpu) != int or type(mem) != int or type(vm_num) != int:
            try:
                vcpu = int(vcpu)
                mem = int(mem)
                vm_num = int(vm_num)
            except:        
                self.error = 'args error.'
                return False
            
        if vcpu < 0 or mem < 0 or vm_num < 0:
            self.error = 'args error.'
            return False
        
        if fake == True:
            return True
        
        with transaction.atomic():
            self.db_obj.vcpu_allocated -= vcpu
            self.db_obj.mem_allocated -= mem
            self.db_obj.vm_created -= vm_num
            if self.db_obj.vcpu_allocated < 0:
                self.db_obj.vcpu_allocated = 0
            if self.db_obj.mem_allocated < 0:
                self.db_obj.mem_allocated = 0
            if self.db_obj.vm_created < 0:
                self.db_obj.vm_created = 0
            try:
                self.db_obj.save()
            except Exception, e:
                self.error = e.message 
                return False
        return True
    
    def managed_by(self, user):
        if user.is_superuser:
            return True
        return user in self.db_obj.group.admin_user.all()
        