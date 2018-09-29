#coding=utf-8
import subprocess
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

        self.ipmi_host = db_obj.ipmi_host
        self.ipmi_user = db_obj.ipmi_user
        self.ipmi_password = db_obj.ipmi_password
        
        self.vlans = [vlan.vlan for vlan in db_obj.vlan.all()]
        self.vlan_types = [(vlan.type.code, vlan.type.name) for vlan in db_obj.vlan.all()]
        
#     def __getattr__(self, name):
#         return self.db_obj.__getattribute__(name)
    
    def alive(self, times=3):
        # cmd = 'ping %s -c %d' % (self.db_obj.ipv4, times)
        cmd = 'fping %s -r %d' % (self.db_obj.ipv4, times)
        res, info = subprocess.getstatusoutput(cmd)
        if res == 0:
            return True
        return False
            
    def claim(self, vcpu, mem, vm_num = 1, fake=False):
        if settings.DEBUG: print('[host]', '宿主机获取资源', vcpu, mem, vm_num, fake)
        if type(vcpu) != int or type(mem) != int or type(vm_num) != int:
            try:
                vcpu = int(vcpu)
                mem = int(mem)
                vm_num = int(vm_num)
            except:
                if settings.DEBUG: print('host claim args error.')     
                self.error = 'args error.'
                return False
        
        if vcpu < 0 or mem < 0 or vm_num < 0:
            if settings.DEBUG: print('host claim args < 0')  
            self.error = 'args error.'
            return False

        res = True
        try:
            with transaction.atomic():
                db = ModelHost.objects.select_for_update().get(pk=self.db_obj.pk)
                if settings.DEBUG: print('[host]', db.vcpu_allocated, db.mem_allocated, db.vm_created)
                if db.mem_allocated + db.mem_reserved + mem > db.mem_total:
                    self.error = 'mem not enough.'
                    res = False

                if res and db.vm_created + vm_num > db.vm_limit:
                    self.error = 'exceed vm limit.'
                    res = False
                
                if res and fake != True:
                    db.vcpu_allocated += vcpu
                    db.mem_allocated += mem
                    db.vm_created += vm_num
                    db.save()
                    if settings.DEBUG: print('[host]', db.vcpu_allocated, db.mem_allocated, db.vm_created)
        except Exception as e:
            if settings.DEBUG: print('host claim.', e.message)  
            self.error = e.message
            res = False
        return res

    def release(self, vcpu, mem, vm_num = 1, fake=False):
        if settings.DEBUG: print('[host]', '宿主机释放资源', vcpu, mem, vm_num, fake)
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
        
        
        try:
            with transaction.atomic():
                db = ModelHost.objects.select_for_update().get(pk=self.db_obj.pk)
                if settings.DEBUG: print('[host]', db.vcpu_allocated, db.mem_allocated, db.vm_created)
                db.vcpu_allocated -= vcpu
                db.mem_allocated -= mem
                db.vm_created -= vm_num
                if db.vcpu_allocated < 0:
                    db.vcpu_allocated = 0
                if db.mem_allocated < 0:
                    db.mem_allocated = 0
                if db.vm_created < 0:
                    db.vm_created = 0
                db.save()
                if settings.DEBUG: print('[host]', db.vcpu_allocated, db.mem_allocated, db.vm_created)
        except Exception as e:
            if settings.DEBUG: print('[host]', '宿主机释放资源操作失败', e)
            self.error = e.message 
            return False
        return True
    
    def managed_by(self, user):
        if user.is_superuser:
            return True
        return user in self.db_obj.group.admin_user.all()
        
    # def br_exists(self, br):
    #     cmd = 'brctl show | grep ^%s | wc -l' % br
    #     res, lines = commands.getstatusoutput(cmd)
    #     if res == 0:
    #         l = int(lines)
    #         if l >0 :
    #             return True
    #     return False

    def _db_fresh(self):
        try:
            obj = ModelHost.objects.select_for_update().get(pk = self.db_obj.pk)
            self.db_obj = obj
        except Exception as e:
            print(e)
    

    def get_pci_device_list(self):
        cmd = 'ssh %s lspci' % self.ipv4
        res, lines = subprocess.getstatusoutput(cmd)
        if settings.DEBUG: print(lines)
        if res == 0:
            return True
        return False  


    def exceed_vm_limit(self):
        return self.vm_created >= self.vm_limit

    def exceed_mem_limit(self, mem=0):
        return self.mem_allocated + int(mem) >= self.mem_total - self.mem_reserved


    def power_off_by_ipmi(self):
        if self.ipmi_host and self.ipmi_user and self.ipmi_password:
            cmd = "ipmitool -I lan -H %(host)s -U %(user)s -P '%(password)s' power off" %{
                'host':self.ipmi_host, 
                'user':self.ipmi_user, 
                'password':self.ipmi_password }
            res, lines = subprocess.getstatusoutput(cmd)
            if settings.DEBUG: print(lines)
            if res == 0:
                return True
        return False  


    def set_enable(self,enable=True):
        try:
            self.db_obj.enable = enable
            self.db_obj.save(update_fields=['enable'])
            return True
        except Exception as e:
            if settings.DEBUG: print(e)
        return False