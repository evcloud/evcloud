from vdisk.manager import VdiskManager, VdiskError
from device.manager import DeviceError, PCIDeviceManager
from compute.managers import HostManager
from utils.errors import VmError, VmNotExistError
from utils import errors
from .manager import VmManager
from .vminstance import VmInstance
from .vm_builder import VmBuilder


class VmAPI:
    """
    虚拟机API
    """
    VmError = VmError

    def __init__(self):
        self._vm_manager = VmManager()
        self._vdisk_manager = VdiskManager()
        self._pci_manager = PCIDeviceManager()

    def _get_user_perms_vm(self, vm_uuid: str, user, related_fields: tuple = ()):
        """
        获取用户有访问权的的虚拟机

        :param vm_uuid: 虚拟机uuid
        :param user: 用户
        :param related_fields: 外键字段；外键字段直接一起获取，而不是惰性的用时再获取
        :return:
            Vm()   # success

        :raises: VmError
        """
        vm = self._vm_manager.get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=related_fields)
        if vm is None:
            raise VmNotExistError(msg='虚拟机不存在')

        if not vm.user_has_perms(user=user):
            raise errors.VmAccessDeniedError(msg='当前用户没有权限访问此虚拟机')

        return vm

    def create_vm(self, image_id: int, vcpu: int, mem: int, vlan_id: int, user, center_id=None, group_id=None,
                  host_id=None, ipv4=None, remarks=None, ip_public=None, sys_disk_size: int = None):
        """
        创建一个虚拟机

        说明：
            center_id和group_id和host_id参数必须给定一个；host_id有效时，使用host_id；host_id无效时，使用group_id；
            ipv4有效时，使用ipv4；ipv4无效时，使用vlan_id；都无效自动分配；

        备注：虚拟机的名称和系统盘名称同虚拟机的uuid

        :param image_id: 镜像id
        :param vcpu: cpu数
        :param mem: 内存大小
        :param vlan_id: 子网id
        :param user: 用户对象
        :param center_id: 分中心id
        :param group_id: 宿主机组id
        :param host_id: 宿主机id
        :param ipv4:  指定要创建的虚拟机ip
        :param remarks: 备注
        :param ip_public: 指定分配公网或私网ip；默认None（不指定），True(公网)，False(私网)
        :param sys_disk_size: 系统盘大小GB
        :return:
            Vm()
            raise VmError

        :raise VmError
        """
        instance = VmInstance.create_instance(
            image_id=image_id, vcpu=vcpu, mem=mem, vlan_id=vlan_id, user=user,
            center_id=center_id, group_id=group_id, host_id=host_id, ipv4=ipv4,
            remarks=remarks, ip_public=ip_public, sys_disk_size=sys_disk_size
        )
        return instance.vm

    def create_vm_for_image(self, image_id: int, vcpu: int, mem: int, host_id=None, ipv4=None):
        """
        为镜像创建一个虚拟机

        说明：
            host_id不能为空，必须为127.0.0.1的宿主机，ipv4可以为镜像专用子网中的任意ip，可以重复使用；

        备注：虚拟机的名称和系统盘名称同虚拟机的uuid

        :param image_id: 镜像id
        :param vcpu: cpu数
        :param mem: 内存大小
        :param host_id: 宿主机id
        :param ipv4:  指定要创建的虚拟机ip
        :return:
            Vm()
            raise VmError

        :raise VmError
        """
        instance = VmInstance.create_instance_for_image(image_id=image_id, vcpu=vcpu, mem=mem, host_id=host_id, ipv4=ipv4)
        return instance.vm

    def delete_vm(self, vm_uuid: str, user=None, force=False):
        """
        删除一个虚拟机

        :param vm_uuid: 虚拟机uuid
        :param user: 用户
        :param force:   是否强制删除， 会强制关闭正在运行的虚拟机
        :return:
            True
            raise VmError

        :raise VmError
        """
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=('host', 'user'))
        return VmInstance(vm=vm).delete(force=force)

    def delete_vm_for_image(self, vm=None):
        """
        删除一个虚拟机

        :param vm_uuid: 虚拟机uuid
        :param user: 用户
        :param force:   是否强制删除， 会强制关闭正在运行的虚拟机
        :return:
            True
            raise VmError

        :raise VmError
        """
        return VmInstance(vm=vm).delete_for_image(force=True)

    def edit_vm_vcpu_mem(self, vm_uuid: str, vcpu: int = 0, mem: int = 0, user=None, force=False):
        """
        修改虚拟机vcpu和内存大小

        :param vm_uuid: 虚拟机uuid
        :param vcpu:要修改的vcpu数，默认0 不修改
        :param mem: 要修改的内存大小，默认0 不修改
        :param user: 用户
        :param force:   是否强制修改, 会强制关闭正在运行的虚拟机
        :return:
            True
            raise VmError

        :raise VmError
        """
        if vcpu < 0 or mem < 0:
            raise errors.VmError.from_error(errors.BadRequestError(msg='vcpu或mem不能小于0'))

        if vcpu == 0 and mem == 0:
            return True

        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=('host', 'user'))
        return VmInstance(vm=vm).edit_vcpu_mem(vcpu=vcpu, mem=mem, force=force)

    def edit_vm_vcpu_mem_for_image(self, vm, vcpu: int = 0, mem: int = 0):
        """
        修改虚拟机vcpu和内存大小

        :param vm_uuid: 虚拟机uuid
        :param vcpu:要修改的vcpu数，默认0 不修改
        :param mem: 要修改的内存大小，默认0 不修改
        :param user: 用户
        :param force:   是否强制修改, 会强制关闭正在运行的虚拟机
        :return:
            True
            raise VmError

        :raise VmError
        """
        if vcpu < 0 or mem < 0:
            raise errors.VmError.from_error(errors.BadRequestError(msg='vcpu或mem不能小于0'))

        if vcpu == 0 and mem == 0:
            return True

        return VmInstance(vm=vm).edit_vcpu_mem(vcpu=vcpu, mem=mem, force=True, update_vm=False)

    def vm_operations(self, vm_uuid: str, op: str, user):
        """
        操作虚拟机

        :param vm_uuid: 虚拟机uuid
        :param op: 操作，['start', 'reboot', 'shutdown', 'poweroff', 'delete', 'delete_force']
        :param user: 用户
        :return:
            True    # success
            False   # failed
        :raise VmError
        """
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=('host', 'user'))
        return VmInstance(vm=vm).operations(op=op)

    def vm_operations_for_image(self, vm, op: str):
        """
        操作虚拟机

        :param vm_uuid: 虚拟机uuid
        :param op: 操作，['start', 'reboot', 'shutdown', 'poweroff', 'delete', 'delete_force']
        :param user: 用户
        :return:
            True    # success
            False   # failed
        :raise VmError
        """
        return VmInstance(vm=vm).operations(op=op)

    def get_vm_status_for_image(self, vm):
        """
        获取虚拟机的运行状态

        :param vm_uuid: 虚拟机uuid
        :param user: 用户
        :return:
            (state_code:int, state_str:str)     # success

        :raise VmError()
        """
        return VmInstance(vm=vm).status()

    def get_vm_status(self, vm_uuid: str, user):
        """
        获取虚拟机的运行状态

        :param vm_uuid: 虚拟机uuid
        :param user: 用户
        :return:
            (state_code:int, state_str:str)     # success

        :raise VmError()
        """
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=('host', 'user'))
        return VmInstance(vm=vm).status()

    def modify_vm_remark(self, vm_uuid: str, remark: str, user):
        """
        修改虚拟机备注信息

        :param vm_uuid: 虚拟机uuid
        :param remark: 新的备注信息
        :param user: 用户
        :return:
            True       # success
        :raise VmError()
        """
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=('host', 'user'))
        return VmInstance(vm=vm).modify_remark(remark=remark)

    def mount_disk(self, vm_uuid: str, vdisk_uuid: str, user):
        """
        向虚拟机挂载硬盘

        *虚拟机和硬盘需要在同一个分中心
        :param vm_uuid: 虚拟机uuid
        :param vdisk_uuid: 虚拟硬盘uuid
        :param user: 用户
        :return:
            Vdisk()    # success

        :raises: VmError
        """
        try:
            vdisk = self._vdisk_manager.get_vdisk_by_uuid(uuid=vdisk_uuid, related_fields=('quota', 'quota__group'))
        except VdiskError as e:
            raise VmError(msg='查询硬盘时错误')

        if vdisk is None:
            raise errors.VmError.from_error(errors.VdiskNotExist())
        if not vdisk.enable:
            raise errors.VmError.from_error(errors.VdiskNotActive())
        if not vdisk.user_has_perms(user=user):
            raise errors.VmError.from_error(errors.VdiskAccessDenied(msg='没有权限访问此硬盘'))

        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=('host__group', 'user'))
        return VmInstance(vm=vm).mount_disk(vdisk=vdisk)

    def umount_disk(self, vdisk_uuid: str, user):
        """
        从虚拟机卸载硬盘

        :param vdisk_uuid: 虚拟硬盘uuid
        :param user: 用户
        :return:
            Vdisk()    # success

        :raises: VmError
        """
        try:
            vdisk = self._vdisk_manager.get_vdisk_by_uuid(uuid=vdisk_uuid, related_fields=('vm', 'vm__host'))
        except VdiskError as e:
            raise VmError(msg='查询硬盘时错误')

        if vdisk is None:
            raise errors.VmError.from_error(errors.VdiskNotExist())

        if not vdisk.user_has_perms(user=user):
            raise errors.VmError.from_error(errors.VdiskAccessDenied(msg='没有权限访问此硬盘'))

        vm = vdisk.vm
        if not vm:
            return vdisk

        if not vm.user_has_perms(user=user):
            raise errors.VmAccessDeniedError(msg='当前用户没有权限访问此虚拟机')

        return VmInstance(vm=vm).umount_disk(vdisk=vdisk)

    def create_vm_sys_snap(self, vm_uuid: str, remarks: str, user):
        """
        创建虚拟机系统盘快照
        :param vm_uuid: 虚拟机id
        :param remarks: 快照备注信息
        :param user: 用户
        :return:
            VmDiskSnap()    # success
        :raises: VmError
        """
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=('user', 'image__ceph_pool__ceph'))
        return VmInstance(vm=vm).create_sys_snap(remarks=remarks)

    def delete_sys_disk_snap(self, snap_id: int, user):
        """
        删除虚拟机系统盘快照

        :param snap_id: 快照id
        :param user: 用户
        :return:
            True    # success

        :raises: VmError
        """
        return VmInstance.delete_sys_disk_snap(snap_id=snap_id, user=user)

    def modify_sys_snap_remarks(self, snap_id: int, remarks: str, user):
        """
        修改虚拟机系统盘快照备注信息

        :param snap_id: 快照id
        :param remarks: 备注信息
        :param user: 用户
        :return:
            VmDiskSnap()    # success
        :raises: VmError
        """
        return VmInstance.modify_sys_snap_remarks(snap_id=snap_id, remarks=remarks, user=user)

    def vm_rollback_to_snap(self, vm_uuid: str, snap_id: int, user):
        """
        回滚虚拟机系统盘到指定快照

        :param vm_uuid: 虚拟机id
        :param snap_id: 快照id
        :param user: 用户
        :return:
           True    # success

        :raises: VmError
        """
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=())
        return VmInstance(vm=vm).rollback_to_snap(snap_id=snap_id)

    def get_user_pci_device(self, device_id: int, user):
        """
        获取用户有权限访问的pci设备

        :param device_id: pci设备id
        :param user: 用户
        :return:
            PCIDevice()    # success

        :raises: VmError
        """
        try:
            device = self._pci_manager.get_device_by_id(device_id=device_id, related_fields=('host',))
        except DeviceError as e:
            raise VmError(msg='查询设备时错误')

        if device is None:
            raise errors.VmError.from_error(errors.DeviceNotFound())

        if not device.enable:
            raise errors.VmError.from_error(errors.DeviceNotActive())

        if not device.user_has_perms(user=user):
            raise errors.VmError.from_error(errors.DeviceAccessDenied(msg='当前用户没有权限访问此设备'))

        return device

    def umount_pci_device(self, device_id: int, user):
        """
        从虚拟机卸载pci设备

        :param device_id: pci设备id
        :param user: 用户
        :return:
            PCIDevice()    # success

        :raises: VmError
        """
        device = self.get_user_pci_device(device_id=device_id, user=user)
        vm = device.vm
        if vm is None:
            return True

        if not vm.user_has_perms(user=user):
            raise errors.VmAccessDeniedError(msg='当前用户没有权限访问此虚拟机')

        return VmInstance(vm=vm).umount_pci_device(device=device)

    def mount_pci_device(self, vm_uuid: str, device_id: int, user):
        """
        向虚拟机挂载pci设备

        :param vm_uuid: 虚拟机uuid
        :param device_id: pci设备id
        :param user: 用户
        :return:
            PCIDevice()   # success

        :raises: VmError
        """
        device = self.get_user_pci_device(device_id=device_id, user=user)
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=('user', 'host__group'))
        return VmInstance(vm=vm).mount_pci_device(device=device)

    def change_sys_disk(self, vm_uuid: str, image_id: int, user):
        """
        更换虚拟机系统镜像

        :param vm_uuid: 虚拟机uuid
        :param image_id: 系统镜像id
        :param user: 用户
        :return:
            Vm()   # success

        :raises: VmError
        """
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=(
            'user', 'host__group', 'image__ceph_pool__ceph'))

        new_image = VmBuilder().get_image(image_id)  # 镜像
        return VmInstance(vm=vm).change_sys_disk(image=new_image)

    def migrate_vm(self, vm_uuid: str, host_id: int, user, force: bool = False):
        """
        迁移虚拟机，迁移后强制更新源与目标Host资源分配信息

        :param vm_uuid: 虚拟机uuid
        :param host_id: 宿主机id
        :param user: 用户
        :param force: True(强制迁移)，False(普通迁移)
        :return:
            Vm()   # success

        :raises: VmError
        """
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=(
            'user', 'host__group', 'image__ceph_pool__ceph'))

        new_vm = VmInstance(vm=vm).migrate(host_id=host_id, force=force)
        HostManager.update_host_quota(host_id=vm.host_id)
        HostManager.update_host_quota(host_id=new_vm.host_id)
        return new_vm

    def reset_sys_disk(self, vm_uuid: str, user):
        """
        重置虚拟机系统盘，恢复到创建时状态

        :param vm_uuid: 虚拟机uuid
        :param user: 用户
        :return:
            Vm()   # success

        :raises: VmError
        """
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=(
            'user', 'host__group', 'image__ceph_pool__ceph'))
        return VmInstance(vm=vm).reset_sys_disk()

    def vm_change_password(self, vm_uuid: str, user, username: str, password: str):
        """
        重置虚拟机系统登录密码

        :param vm_uuid: 虚拟机uuid
        :param user: 用户
        :param username: 用户名
        :param password: 新密码
        :return:
            Vm()   # success

        :raises: VmError
        """
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=('host', 'user', 'image'))
        return VmInstance(vm).change_password(username=username, password=password)

    def vm_miss_fix(self, vm_uuid: str, user):
        """
        宿主机上虚拟机丢失修复

        :param vm_uuid: 虚拟机uuid
        :param user: 用户
        :return:
            Vm()   # success

        :raises: VmError
        """
        vm = self._get_user_perms_vm(
            vm_uuid=vm_uuid, user=user, related_fields=('host', 'user', 'image__ceph_pool__ceph'))
        return VmInstance(vm).miss_fix()

    def live_migrate_vm(self, vm_uuid: str, dest_host_id: int, user):
        """
        迁移虚拟机，迁移后强制更新源与目标Host资源分配信息

        :param vm_uuid: 虚拟机uuid
        :param dest_host_id: 目标宿主机id
        :param user: 用户
        :return:
            MigrateTask()   # success

        :raises: VmError
        """
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=(
            'user', 'host__group', 'image__ceph_pool__ceph'))
        task = VmInstance(vm).live_migrate(dest_host_id=dest_host_id)
        HostManager.update_host_quota(host_id=vm.host_id)
        HostManager.update_host_quota(host_id=dest_host_id)
        return task

    def get_vm_stats(self, vm_uuid: str, user):
        """
        查询vm内存，硬盘io，网络io等信息

        :raises: VmError
        """
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=('host',))
        return VmInstance(vm).get_stats()

    def vm_sys_disk_expand(self, vm_uuid: str, expand_size: int, user):
        """
        vm系统盘扩容，系统盘最大5Tb

        :param expand_size: 在原有大小基础上扩容大小， GB
        :return:    vm
        :raises: VmError
        """
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=('image__ceph_pool__ceph',))
        return VmInstance(vm).sys_disk_expand(expand_size)
