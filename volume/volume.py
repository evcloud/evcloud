#coding=utf-8
from .models import DBCephVolume
from api.error import Error, ERR_VOLUME_ID

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

    def mount(self, vmid):
        pass

    def umount(self, vmid):
        pass

    def resize(self, size):
        try:
            self._db.size = size
            self._db.save()
        except:
            return False
        return True

    def remark(self, content):
        try:
            self._db.remarks = content
            self._db.save()
        except:
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
    def dev(self):
        if self._db:
            return self._db.dev
        return None


    @property
    def xml_tpl(self):
        return '''
<disk type='%(type)s' device='%(device)s'>
      <driver name='%(driver)s'/>
      <auth username='%(auth_user)s'>
        <secret type='%(auth_type)s' uuid='%(auth_uuid)s'/>
      </auth>
      <source protocol='%(source_protocol)s' name='%(pool)s/%(name)s'>
        <host name='%(host)s' port='%(port)s'/>
      </source>
      <target dev='%(dev)s' bus='virtio'/>
</disk>
'''
    
        
    
