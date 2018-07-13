#coding=utf-8
from datetime import datetime
from storage.api import StorageAPI
from vmuser.api import API as UserAPI
from compute.api import VmAPI
from compute.api import GroupAPI
from api.error import Error
from api.error import ERR_INT_VOLUME_SIZE
from api.error import ERR_PERM_DEL_VOLUME
from api.error import ERR_DEL_MOUNTED_VOLUME
from api.error import ERR_CEPH_RM
from api.error import ERR_CEPH_MV
from api.error import ERR_CEPH_RESIZE
from api.error import ERR_VOLUME_CREATE_NOPOOL
from api.error import ERR_VOLUME_QUOTA_G
from api.error import ERR_VOLUME_QUOTA_V
from .manager import CephManager
from .quota import CephQuota


class VolumeAPI(object):
    def __init__(self, manager=None, storage_api=None, vm_api=None, group_api=None, quota=None):
        if not manager:
            self.manager = CephManager()
        else:
            self.manager = manager
        if not storage_api:
            self.storage_api = StorageAPI()
        else:
            self.storage_api = storage_api
        if not vm_api:
            self.vm_api = VmAPI()
        else:
            self.vm_api = vm_api
        if not group_api:
            self.group_api = GroupAPI()
        else:
            self.group_api = group_api
        if not quota:
            self.quota = CephQuota()
        else:
            self.quota = quota

        super().__init__()

    def create(self, pool_id, size, group_id=None):
        cephpool = self.storage_api.get_pool_by_id(pool_id)
        if not cephpool:
            raise Error(ERR_VOLUME_CREATE_NOPOOL)

        if type(size) != int or size <= 0:
            raise Error(ERR_INT_VOLUME_SIZE)

        return self.manager.create_volume(cephpool, size, group_id)

    def delete(self, volume_id, force=False):
        volume = self.get_volume_by_id(volume_id)
        if volume.vm:
            raise Error(ERR_DEL_MOUNTED_VOLUME)
        cephpool_id = volume.cephpool_id
        tmp_volume_name = 'x_{}_{}'.format(datetime.now().strftime("%Y%m%d%H%M%S"), volume_id)
        if self.storage_api.mv(cephpool_id, volume_id, tmp_volume_name):
            if not volume.delete():
                self.storage_api.mv(cephpool_id, tmp_volume_name, volume_id)
                return False

            if force == True:
                if not self.storage_api.rm(cephpool_id, tmp_volume_name):
                    print(ERR_CEPH_RM)
        else:
            raise Error(ERR_CEPH_MV)
        return True
        
    def resize(self, volume_id, size):
        volume = self.get_volume_by_id(volume_id)
        #if not self.quota.group_quota_validate(volume.group_id, size, volume.size):
        if not self.quota.group_pool_quota_validate(volume.group_id, volume.cephpool_id, size, volume.size):
            raise Error(ERR_VOLUME_QUOTA_G)
        # if not self.quota.volume_quota_validate(volume.group_id, size):
        if not self.quota.volume_pool_quota_validate(volume.group_id, volume.cephpool_id, size):
            raise Error(ERR_VOLUME_QUOTA_V)
        if self.storage_api.resize(volume.cephpool_id, volume.id, size):
            return volume.resize(size)
        else:
            raise Error(ERR_CEPH_RESIZE)
        

    def _get_disk_xml(self, volume, dev):
        cephpool = self.storage_api.get_pool_by_id(volume.cephpool_id)

        xml = volume.xml_tpl % {
            'driver': 'qemu',
            'auth_user': cephpool.username,
            'auth_type': 'ceph',
            'auth_uuid': cephpool.uuid,
            'source_protocol': 'rbd',
            'pool': cephpool.pool,
            'name': volume.id,
            'host': cephpool.host,
            'port': cephpool.port,
            'dev': dev
        }
        return xml

    def mount(self, vm_uuid, volume_id):
        volume = self.get_volume_by_id(volume_id)
        vm = self.vm_api.get_vm_by_uuid(vm_uuid)
        if vm.group_id != volume.group_id:
            return False

        disk_list = vm.get_disk_list()
        mounted_volume_list = self.get_volume_list(vm_uuid=vm_uuid)
        for v in mounted_volume_list:
            disk_list.append(v.dev)
        print(disk_list)
        i = 0
        while True:
            j = i
            d = ''
            while True:
                d += chr(ord('a') + j % 26)
                j //= 26
                if j <= 0:
                    break
            if not 'vd' + d in disk_list:
                dev = 'vd' + d
                break
            i+=1

        xml = self._get_disk_xml(volume, dev)
        print(xml)
        if volume.mount(vm_uuid, dev):
            try:
                if self.vm_api.attach_device(vm_uuid, xml):
                    return True
            except Error as e:
                volume.umount()
                raise e
        return False

    def umount(self, volume_id):
        volume = self.get_volume_by_id(volume_id)
        vm_uuid = volume.vm
        if self.vm_api.vm_uuid_exists(vm_uuid):
            vm = self.vm_api.get_vm_by_uuid(vm_uuid)
            disk_list = vm.get_disk_list()
            if not volume.dev in disk_list:
                if volume.umount():
                    return True
                return False
            xml = self._get_disk_xml(volume, volume.dev)
            if self.vm_api.detach_device(vm_uuid, xml):
                try:
                    if volume.umount():
                        return True
                except Error as e:
                    self.vm_api.attach_device(vm_uuid, xml)
                    raise e
        else:
            if volume.umount():
                return True
        return False

    def set_remark(self, volume_id, content):
        volume = self.get_volume_by_id(volume_id)
        return volume.set_remark(content)

    def get_volume_list_by_pool_id(self, cephpool_id):
        cephpool = self.storage_api.get_pool_by_id(cephpool_id)
        return self.manager.get_volume_list(cephpool_id=cephpool_id)
        
    def get_volume_list_by_user_id(self, user_id):
        return self.manager.get_volume_list(user_id=user_id)

    def get_volume_list_by_group_id(self, group_id):
        return self.manager.get_volume_list(group_id=group_id)

    def get_volume_list_by_vm_uuid(self, vm_uuid):
        return self.manager.get_volume_list(vm_uuid=vm_uuid)
        
    def get_volume_list(self, user_id=None, creator=None, cephpool_id=None, group_id=None, vm_uuid=None):
        return self.manager.get_volume_list(user_id=user_id, creator=creator, cephpool_id=cephpool_id, group_id=group_id, vm_uuid=vm_uuid)

    def get_volume_by_id(self, volume_id):
        return self.manager.get_volume_by_id(volume_id)

    def set_user_id(self, volume_id, user_id):
        volume = self.get_volume_by_id(volume_id)
        return volume.set_user_id(user_id)

    def set_group_id(self, volume_id, group_id):
        volume = self.get_volume_by_id(volume_id)
        return volume.set_group_id(group_id)






