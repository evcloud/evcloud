#coding=utf-8
from .manager import VdiskError, Manager as VdiskManager
from .quota import Quota
from datetime import datetime
from ceph.api import CephAPI
from vms.api import VmAPI
from compute.api import GroupAPI


class VdiskAPI(object):
    def __init__(self, manager=None, ceph_api=None, vm_api=None, group_api=None, quota=None):
        if not manager:
            self.manager = VdiskManager()
        else:
            self.manager = manager
        if not ceph_api:
            self.ceph_api = CephAPI()
        else:
            self.ceph_api = ceph_api
        if not vm_api:
            self.vm_api = VmAPI()
        else:
            self.vm_api = vm_api
        if not group_api:
            self.group_api = GroupAPI()
        else:
            self.group_api = group_api
        if not quota:
            self.quota = Quota()
        else:
            self.quota = quota

        super().__init__()

    def create(self, pool_id, size, group_id=None):
        cephpool = self.ceph_api.get_pool_by_id(pool_id)
        if not cephpool:
            raise VdiskError(msg='云硬盘创建失败，无资源池')

        if type(size) != int or size <= 0:
            raise VdiskError(msg='磁盘容量参数必须为正整数')

        return self.manager.create_vdisk(cephpool, size, group_id)

    def delete(self, vdisk_id, force=False):
        vdisk = self.get_vdisk_by_id(vdisk_id)
        if vdisk.vm:
            raise VdiskError(msg='不能删除已挂载VDISK')
        cephpool_id = vdisk.cephpool_id
        tmp_vdisk_name = 'x_{}_{}'.format(datetime.now().strftime("%Y%m%d%H%M%S"), vdisk_id)
        if self.ceph_api.mv(cephpool_id, vdisk_id, tmp_vdisk_name):
            if not vdisk.delete():
                self.ceph_api.mv(cephpool_id, tmp_vdisk_name, vdisk_id)
                return False

            if force == True:
                if not self.ceph_api.rm(cephpool_id, tmp_vdisk_name):
                    print(VdiskError(msg='ceph mv操作失败'))
        else:
            raise VdiskError(msg='ceph mv操作失败')
        return True
        
    def resize(self, vdisk_id, size):
        vdisk = self.get_vdisk_by_id(vdisk_id)
        #if not self.quota.group_quota_validate(vdisk.group_id, size, vdisk.size):
        if not self.quota.group_pool_quota_validate(vdisk.group_id, vdisk.cephpool_id, size, vdisk.size):
            raise VdiskError(msg='集群容量超配额')
        # if not self.quota.vdisk_quota_validate(vdisk.group_id, size):
        if not self.quota.vdisk_pool_quota_validate(vdisk.group_id, vdisk.cephpool_id, size):
            raise VdiskError(msg='云硬盘容量超配额')
        if self.ceph_api.resize(vdisk.cephpool_id, vdisk.id, size):
            return vdisk.resize(size)
        else:
            raise VdiskError(msg='ceph resize操作失败')
        

    def _get_disk_xml(self, vdisk, dev):
        cephpool = self.ceph_api.get_pool_by_id(vdisk.cephpool_id)

        xml = vdisk.xml_tpl % {
            'driver': 'qemu',
            'auth_user': cephpool.username,
            'auth_type': 'ceph',
            'auth_uuid': cephpool.uuid,
            'source_protocol': 'rbd',
            'pool': cephpool.pool,
            'name': vdisk.id,
            'host': cephpool.host,
            'port': cephpool.port,
            'hosts_xml': cephpool.hosts_xml,
            'dev': dev
        }
        return xml

    def mount(self, vm_uuid, vdisk_id):
        vdisk = self.get_vdisk_by_id(vdisk_id)
        vm = self.vm_api.get_vm_by_uuid(vm_uuid)
        if vm.group_id != vdisk.group_id:
            return False

        disk_list = vm.get_disk_list()
        mounted_vdisk_list = self.get_vdisk_list(vm_uuid=vm_uuid)
        for v in mounted_vdisk_list:
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

        xml = self._get_disk_xml(vdisk, dev)
        print(xml)
        if vdisk.mount(vm_uuid, dev):
            try:
                if self.vm_api.attach_device(vm_uuid, xml):
                    return True
            except Exception as e:
                vdisk.umount()
                raise VdiskError(err=e)
        return False

    def umount(self, vdisk_id):
        vdisk = self.get_vdisk_by_id(vdisk_id)
        vm_uuid = vdisk.vm
        if self.vm_api.vm_uuid_exists(vm_uuid):
            vm = self.vm_api.get_vm_by_uuid(vm_uuid)
            disk_list = vm.get_disk_list()
            if not vdisk.dev in disk_list:
                if vdisk.umount():
                    return True
                return False
            xml = self._get_disk_xml(vdisk, vdisk.dev)
            if self.vm_api.detach_device(vm_uuid, xml):
                try:
                    if vdisk.umount():
                        return True
                except Exception as e:
                    self.vm_api.attach_device(vm_uuid, xml)
                    raise VdiskError(err=e)
        else:
            if vdisk.umount():
                return True
        return False

    def set_remark(self, vdisk_id, content):
        vdisk = self.get_vdisk_by_id(vdisk_id)
        return vdisk.set_remark(content)

    def get_vdisk_list_by_pool_id(self, cephpool_id):
        return self.manager.get_vdisk_list(cephpool_id=cephpool_id)
        
    def get_vdisk_list_by_user_id(self, user_id):
        return self.manager.get_vdisk_list(user_id=user_id)

    def get_vdisk_list_by_group_id(self, group_id):
        return self.manager.get_vdisk_list(group_id=group_id)

    def get_vdisk_list_by_vm_uuid(self, vm_uuid):
        return self.manager.get_vdisk_list(vm_uuid=vm_uuid)
        
    def get_vdisk_list(self, user_id=None, creator=None, cephpool_id=None, group_id=None, vm_uuid=None):
        return self.manager.get_vdisk_list(user_id=user_id, creator=creator, cephpool_id=cephpool_id, group_id=group_id, vm_uuid=vm_uuid)

    def get_vdisk_by_id(self, vdisk_id):
        return self.manager.get_vdisk_by_id(vdisk_id)

    def set_user_id(self, vdisk_id, user_id):
        vdisk = self.get_vdisk_by_id(vdisk_id)
        return vdisk.set_user_id(user_id)

    def set_group_id(self, vdisk_id, group_id):
        vdisk = self.get_vdisk_by_id(vdisk_id)
        return vdisk.set_group_id(group_id)






