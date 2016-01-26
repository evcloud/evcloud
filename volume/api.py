#coding=utf-8
from storage.api import CephStorageAPI
from vmuser.api import API as UserAPI
from compute.api import VmAPI
from api.error import Error, ERR_INT_VOLUME_SIZE, ERR_PERM_DEL_VOLUME
from .manager import CephManager

class CephVolumeAPI(object):
    def __init__(self, manager=None, storage_api=None, vm_api=None):
        if not manager:
            self.manager = CephManager()
        else:
            self.manager = manager
        if not storage_api:
            self.storage_api = CephStorageAPI()
        else:
            self.storage_api = storage_api
        if not vm_api:
            self.vm_api = VmAPI()
        else:
            self.vm_api = vm_api

        super().__init__()

    def create(self, cephpool_id, size):
        cephpool = self.storage_api.get_pool_by_id(cephpool_id)
        if type(size) != int or size <= 0:
            raise Error(ERR_INT_VOLUME_SIZE)
        volume_id = self.manager.create_volume(cephpool, size)
        return volume_id

    def delete(self, volume_id, force=False):
        volume = self.get_volume_by_id(volume_id)

        storage_delete_success = False
        if force == True:
            if self.storage_api.rm(volume.cephpool_id, volume.id):
                storage_delete_success = True
        else:
            if self.storage_api.mv(volume.cephpool_id, volume.id, 'x_' + volume.id):
                storage_delete_success = True
        if storage_delete_success:
            return volume.delete()
        return False

    def resize(self, volume_id, size):
        volume = self.get_volume_by_id(volume_id)
        if self.storage_api.resize(volume.cephpool_id, volume.id, size):
            return volume.resize(size)
        return False

    def _get_disk_dev(self, vmid):
        return 'vdb'

    def _get_disk_xml(self, volume):
        cephpool = self.storage_api.get_pool_by_id(volume.cephpool_id)

        xml = volume.xml_tpl % {
            'type': 'network',
            'device': 'disk',
            'driver': 'qemu',
            'auth_user': cephpool.username,
            'auth_type': 'ceph',
            'auth_uuid': cephpool.uuid
            'source_protocol': 'rbd',
            'pool': cephpool.pool,
            'name': volume.id,
            'host': cephpool.host,
            'port': cephpool.port,
            'dev': self._get_disk_dev(vmid)
        }
        return xml

    def mount(self, volume_id, vmid):
        volume = self.get_volume_by_id(volume_id)
        xml = self._get_disk_xml(volume)
        if vm.mount(vmid, xml):
            return volume.mount(vmid)
        return False

    def umount(self, volume_id, vmid):
        volume = self.get_volume_by_id(volume_id)
        xml = self._get_disk_xml(volume)
        if vm.umount(vmid, xml):
            return volume.umount(vmid)
        return False

    def remark(self, volume_id, content):
        volume = self.get_volume_by_id(volume_id)
        return volume.remark(content)

    def get_volume_list_by_pool_id(self, cephpool_id):
        cephpool = self.storage_api.get_pool_by_id(cephpool_id)
        return self.manager.get_volume_list(cephpool_id=cephpool_id)
        
    def get_volume_list_by_user_id(self, user_id):
        return self.manager.get_volume_list(user_id=user_id)
        
    def get_volume_list(self):
        return self.manager.get_volume_list()

    def get_volume_by_id(self, volume_id):
        return self.manager.get_volume_by_id(volume_id)






