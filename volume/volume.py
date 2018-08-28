#coding=utf-8
from .models import DBCephVolume
from api.error import Error, ERR_VOLUME_ID
from django.db import transaction
from django.utils import timezone

class CephVolume(object):
    def __init__(self, db=None, volume_id=None):
        if db:
            self._db = db
        elif volume_id:
            try:
                self._db = DBCephVolume.objects.get(pk=volume_id)
            except:
                raise Error(ERR_VOLUME_ID)
        super().__init__()

    def mount(self, vm_uuid, dev):
        res = True
        try:
            with transaction.atomic():
                db = DBCephVolume.objects.select_for_update().get(pk = self._db.pk)
                if db.vm == None and db.enable == True:
                    db.vm = vm_uuid
                    db.attach_time = timezone.now()
                    db.dev = dev
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
                db = DBCephVolume.objects.select_for_update().get(pk = self._db.pk)
                print(db)
                if db.enable == True:
                    db.vm = None
                    db.attach_time = None
                    db.dev = None
                    db.save()
                    self._db = db
                else:
                    res = False
        except Exception as e:
            res = False
        return res  

    def resize(self, size):
        try:
            self._db.size = size
            self._db.save()
        except:
            return False
        return True

    def set_remark(self, content):
        try:
            self._db.remarks = content
            self._db.save()
        except:
            print(111111111111)
            return False
        return True

    def delete(self):
        try:
            self._db.delete()
        except:
            return False
        return True

    @property
    def administrator(self):
        return self._db.user.username

    @property
    def id(self):
        if self._db:
            return self._db.uuid
        return None

    @property
    def size(self):
        if self._db:
            return self._db.size
        return None

    @property
    def cephpool_id(self):
        if self._db:
            return self._db.cephpool_id
        return None

    @property
    def vm(self):
        if self._db:
            return self._db.vm
        return None

    @property
    def attach_time(self):
        return self._db.attach_time
    

    @property
    def dev(self):
        if self._db:
            return self._db.dev
        return None

    @property
    def user_id(self):
        return self._db.user_id

    @property
    def user_name(self):
        return self._db.user and self._db.user.username

    @property
    def group_id(self):
        return self._db.group_id

    @property
    def group_name(self):
        return self._db.group.name
    
    
    @property
    def create_time(self):
        return self._db.create_time
    
    @property
    def remarks(self):
        return self._db.remarks
    
    @property
    def enable(self):
        return self._db.enable
    
    
    def set_user_id(self, user_id):
        try:
            self._db.user_id = user_id
            self._db.save()
        except:
            return False
        return True

    def set_group_id(self, group_id):
        try:
            self._db.group_id = group_id
            self._db.save()
        except:
            return False
        return True
    


    @property
    def xml_tpl(self):
        if self._db.cephpool.host.backend == self._db.cephpool.host.CEPH:
            return '''
<disk type='network' device='disk'>
      <driver name='%(driver)s'/>
      <auth username='%(auth_user)s'>
        <secret type='%(auth_type)s' uuid='%(auth_uuid)s'/>
      </auth>
      <source protocol='%(source_protocol)s' name='%(pool)s/%(name)s'>
        <!--<host name='%(host)s' port='%(port)s'/>-->
        %(hosts_xml)s
      </source>
        <target dev='%(dev)s' bus='virtio'/>   
</disk>
'''
        else:
            return '''
<disk type='block' device='disk'>
    <driver name='qemu' type='qcow2'/>
   <source dev='%(pool)s/%(name)s'/>
   <target dev='%(dev)s' bus='virtio'/>
</disk>            
'''
  
    def managed_by(self, user):
        if user.is_superuser:
            return True
        return user == self._db.user
        
    
