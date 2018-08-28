#coding=utf-8
from .models import DBGPU
from api.error import Error
from api.error import ERR_GPU_ID
from api.error import ERR_GPU_ADDRESS
from django.db import transaction
from django.utils import timezone

class GPU(object):
    def __init__(self, db=None, db_id=None):
        if db:
            self._db = db
        elif db_id:
            try:
                self._db = DBGPU.objects.get(pk=db_id)
            except:
                raise Error(ERR_GPU_ID)
        
        address = self._db.address.split(':')
        if len(address) != 4:
            raise Error(ERR_GPU_ADDRESS)
        self._domain = address[0]
        self._bus = address[1]
        self._slot = address[2]
        self._function = address[3]

        super().__init__()

    def set_remarks(self, content):
        try:
            self._db.remarks = content
            self._db.save()
        except:
            return False
        return True

    def mount(self, vm_id):
        res = True
        try:
            with transaction.atomic():
                db = DBGPU.objects.select_for_update().get(pk = self._db.pk)
                if db.vm == None and db.enable == True:
                    db.vm = vm_id
                    db.attach_time = timezone.now()
                    db.save()
                    self._db = db
                else:
                    res = False
        except:
            res = False
        return res

    def umount(self):
        res = True
        try:
            with transaction.atomic():
                db = DBGPU.objects.select_for_update().get(pk = self._db.pk)
                if db.enable == True:
                    db.vm = None
                    db.attach_time = None
                    db.save()
                    self._db = db
                else:
                    res = False
        except:
            res = False
        return res        

    def set_enable(self):
        res = True
        try:
            with transaction.atomic():
                db = DBGPU.objects.select_for_update().get(pk = self._db.pk)
                db.enable = True
                db.save()
                self._db = db
        except:
            res = False
        return res 

    def set_disable(self):
        res = True
        try:
            with transaction.atomic():
                db = DBGPU.objects.select_for_update().get(pk = self._db.pk)
                db.enable = False
                db.save()
                self._db = db
        except:
            res = False
        return res 

    @property
    def host_ipv4(self):
        return self._db.host.ipv4

    @property
    def host_id(self):
        return self._db.host_id
    
    
    @property
    def address(self):
        return self._db.address

    @property
    def vm(self):
        return self._db.vm

    @property
    def id(self):
        return self._db.id
    

    @property
    def attach_time(self):
        return self._db.attach_time
    
    @property
    def domain(self):
        return self._domain

    @property
    def bus(self):
        return self._bus
    
    @property
    def slot(self):
        return self._slot
    
    @property
    def function(self):
        return self._function
    

    @property
    def administrator(self):
        return self._db.user.username

    @property
    def enable(self):
        return self._db.enable

    @property
    def remarks(self):
        return self._db.remarks
    
    

    @property
    def xml_tpl(self):
        return '''
<hostdev mode='%(mode)s' type='%(type)s' managed='yes'>
    <source>
        <address domain='0x%(domain)s' bus='0x%(bus)s' slot='0x%(slot)s' function='0x%(function)s'/>
    </source>
</hostdev>
'''

    @property
    def xml_desc(self):
        return self.xml_tpl % {
            'mode': 'subsystem',
            'type': 'pci',
            'managed': 'yes',
            'domain': self.domain,
            'bus': self.bus,
            'slot': self.slot,
            'function': self.function
        } 
        
    def managed_by(self, user):
        if user.is_superuser:
            return True
        return user in self._db.host.group.admin_user.all()