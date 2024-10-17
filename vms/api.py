from func_timeout import FunctionTimedOut

from logrecord.manager import user_operation_record, LogManager
from logrecord.models import LogRecord
from vdisk.manager import VdiskManager, VdiskError
from device.manager import DeviceError, PCIDeviceManager
from compute.managers import HostManager
from utils.errors import VmError, VmNotExistError
from utils import errors
from utils.vm_normal_status import vm_normal_status
from ceph.managers import check_resource_permissions
from .manager import VmManager, AttachmentsIPManager, VmSharedUserManager
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

    @staticmethod
    def check_user_permissions_of_vm(
            vm, user, allow_superuser: bool, allow_resource: bool, allow_owner: bool = True,
            allow_shared_perm: str = None
    ):
        """
        :param vm: 云主机对象
        :param user: 用户对象
        :param allow_superuser: True(允许超级管理员)
        :param allow_resource: True(允许资源管理员)
        :param allow_owner: True(允许资源所有者)
        :param allow_shared_perm:
            VmSharedUserManager.SHARED_PERM_READ: 允许有读权限的资源共享用户
            VmSharedUserManager.SHARED_PERM_WRITE: 允许有写权限的资源共享用户
            其他忽略不允许
        :ratuen:
            True    # 满足权限
            raise VmAccessDeniedError # 没有权限

        :raises: VmAccessDeniedError
        """
        return VmInstance.check_user_permissions_of_vm(
            vm=vm, user=user,
            allow_superuser=allow_superuser, allow_resource=allow_resource, allow_owner=allow_owner,
            allow_shared_perm=allow_shared_perm
        )

    @staticmethod
    def check_user_permissions_of_disk(
            disk, user,
            allow_superuser: bool, allow_resource: bool, allow_owner: bool = True
    ):
        """
        :param disk: 云硬盘对象
        :param user: 用户对象
        :param allow_superuser: True(允许超级管理员)
        :param allow_resource: True(允许资源管理员)
        :param allow_owner: True(允许资源所有者)
        :ratuen:
            True    # 满足权限
            raise VmAccessDeniedError # 没有权限

        :raises: VmAccessDeniedError
        """
        if allow_superuser and user.is_superuser:
            return True

        if allow_owner and disk.user_id == user.id:
            return True

        if allow_resource and check_resource_permissions(user=user):
            return True

        raise errors.VdiskAccessDenied(msg='当前用户没有权限访问此云硬盘')

    def _get_user_perms_vm(
            self, vm_uuid: str, user, related_fields: tuple = (), flag=False, query_user=True,
            allow_superuser=True, allow_resource=False, allow_owner=True, allow_shared_perm: str = None
    ):
        """
        获取用户有访问权的的虚拟机

        :param vm_uuid: 虚拟机uuid
        :param user: 用户
        :param related_fields: 外键字段；外键字段直接一起获取，而不是惰性的用时再获取
        :param flag: 用于虚拟机在搁置的情况下，对一些情况允许
        :param query_user: 查询虚拟机用户 目前仅限于虚拟机状态的查询可用不要查询虚拟机的用户信息
        :param allow_superuser: True(允许超级管理员)
        :param allow_resource: True(允许资源管理员)
        :param allow_owner: True(允许资源所有者)
        :param allow_shared_perm:
            VmSharedUserManager.SHARED_PERM_READ: 允许有读权限的资源共享用户
            VmSharedUserManager.SHARED_PERM_WRITE: 允许有写权限的资源共享用户
            其他忽略不允许
        :return:
            Vm()   # success

        :raises: VmError
        """
        vm = self._vm_manager.get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=related_fields)
        if vm is None:
            raise VmNotExistError(msg='虚拟机不存在')

        if query_user:
            self.check_user_permissions_of_vm(
                vm=vm, user=user,
                allow_superuser=allow_superuser, allow_resource=allow_resource, allow_owner=allow_owner,
                allow_shared_perm=allow_shared_perm
            )

        status_bool = vm_normal_status(vm=vm, flag=flag)
        if status_bool is False:
            raise errors.VmAccessDeniedError(msg='虚拟机搁置状态， 拒绝此操作')

        return vm

    def create_vm(self, image_id: int, vcpu: int, mem: int, vlan_id: int, user, center_id=None, group_id=None,
                  host_id=None, ipv4=None, remarks=None, ip_public=None, sys_disk_size: int = None, owner=None):
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
        :param center_id: 数据中心id
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
            remarks=remarks, ip_public=ip_public, sys_disk_size=sys_disk_size, owner=owner
        )
        return instance.vm

    def create_vm_for_image(self, image_id: int, vcpu: int, mem: int, host_id=None, ipv4=None):
        """
        为镜像创建一个虚拟机

        说明：
            host_id不能为空，宿主机有原来127.0.0.1 修改为任意，ipv4可以为镜像专用子网中的任意ip，可以重复使用；

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

    def delete_vm(self, vm_uuid: str, request, user=None, force=False):
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
        vm = self._get_user_perms_vm(
            vm_uuid=vm_uuid, user=user, related_fields=('host', 'user'),
            allow_superuser=True, allow_resource=True, allow_owner=False
        )
        self.vm_operation_log(request=request, operation_content=f'删除云主机, 云主机IP：{vm.mac_ip}')
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

    def edit_vm_vcpu_mem(self, vm_uuid: str, request, vcpu: int = 0, mem: int = 0, user=None, force=False):
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

        vm = self._get_user_perms_vm(
            vm_uuid=vm_uuid, user=user, related_fields=('host', 'user'),
            allow_superuser=True, allow_resource=True, allow_owner=False
        )

        self.vm_operation_log(request=request, operation_content=f'修改云主机vcpu和内存大小，云主机IP：{vm.mac_ip}, 内存修改为{mem}, vcpu修改为{vcpu}')
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

    def vm_operations(self, vm_uuid: str, request, op: str, user):
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
        if op in ['delete', 'delete_force']:
            vm = self._get_user_perms_vm(
                vm_uuid=vm_uuid, user=user, related_fields=('host', 'user'),
                allow_superuser=True, allow_resource=True, allow_owner=False
            )
        else:
            vm = self._get_user_perms_vm(
                vm_uuid=vm_uuid, user=user, related_fields=('host', 'user'),
                allow_superuser=True, allow_resource=True, allow_owner=True,
                allow_shared_perm=VmSharedUserManager.SHARED_PERM_WRITE
            )

        ops_dict = {
            'start': '启动云主机',
            'reboot': '重启云主机',
            'shutdown': '关闭云主机',
            'poweroff': '云主机断电',
            'delete': '删除云主机',
            'delete_force': '强制删除云主机',
        }

        self.vm_operation_log(request=request, operation_content=f'{ops_dict[op]}, 云主机IP: {vm.mac_ip}')

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
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=('host', 'user'), query_user=False)
        return VmInstance(vm=vm).status()

    def modify_vm_remark(self, vm_uuid: str, remark: str, user, request):
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

        self.vm_operation_log(request=request, operation_content=f'修改云主机备注信息, 云主机IP: {vm.mac_ip}, 备注信息为：{remark}')
        return VmInstance(vm=vm).modify_remark(remark=remark)

    def mount_disk(self, vm_uuid: str, vdisk_uuid: str, request, user):
        """
        向虚拟机挂载硬盘

        *虚拟机和硬盘需要在同一个数据中心
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

        try:
            self.check_user_permissions_of_disk(
                disk=vdisk, user=request.user,
                allow_superuser=True, allow_resource=True, allow_owner=False
            )
        except errors.Error as exc:
            raise errors.VmError.from_error(errors.VdiskAccessDenied(msg='没有权限挂载此硬盘'))

        vm = self._get_user_perms_vm(
            vm_uuid=vm_uuid, user=user, related_fields=('host__group', 'user'),
            allow_superuser=True, allow_resource=True, allow_owner=False
        )

        self.vm_operation_log(request=request, operation_content=f'挂载云硬盘, 云主机IP: {vm.mac_ip}, 云硬盘id：{vdisk_uuid}')

        return VmInstance(vm=vm).mount_disk(vdisk=vdisk)

    def umount_disk(self, vdisk_uuid: str, request, user):
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

        try:
            self.check_user_permissions_of_disk(
                disk=vdisk, user=request.user,
                allow_superuser=True, allow_resource=True, allow_owner=False
            )
        except errors.Error as exc:
            raise errors.VmError.from_error(errors.VdiskAccessDenied(msg='没有权限卸载此硬盘'))

        status_bool = vm_normal_status(vm=vdisk.vm)
        if status_bool is False:
            raise errors.VmAccessDeniedError(msg='虚拟机搁置状态， 拒绝此操作')

        vm = vdisk.vm
        if not vm:
            return vdisk

        try:
            self.check_user_permissions_of_vm(
                vm=vm, user=request.user,
                allow_superuser=True, allow_resource=True, allow_owner=False
            )
        except errors.Error as exc:
            raise errors.VmAccessDeniedError(msg='当前用户没有权限访问此虚拟机')

        self.vm_operation_log(request=request, operation_content=f'卸载云硬盘, 云主机IP: {vm.mac_ip}, 云硬盘id：{vdisk_uuid}')

        return VmInstance(vm=vm).umount_disk(vdisk=vdisk)

    def create_vm_sys_snap(self, vm_uuid: str, remarks: str, user, request):
        """
        创建虚拟机系统盘快照
        :param vm_uuid: 虚拟机id
        :param remarks: 快照备注信息
        :param user: 用户
        :return:
            VmDiskSnap()    # success
        :raises: VmError
        """
        vm = self._get_user_perms_vm(
            vm_uuid=vm_uuid, user=user, related_fields=('user', 'image__ceph_pool__ceph'),
            allow_superuser=True, allow_resource=True, allow_owner=False
        )

        vm_snap = VmInstance(vm=vm).create_sys_snap(remarks=remarks)
        self.vm_operation_log(request=request, operation_content=f'创建云主机系统盘快照, 云主机IP: {vm.mac_ip}, 快照ID：{vm_snap.id}',
                              remark=remarks)

        return vm_snap

    def delete_sys_disk_snap(self, snap_id: int, user, request):
        """
        删除虚拟机系统盘快照

        :param snap_id: 快照id
        :param user: 用户
        :return:
            True    # success

        :raises: VmError
        """

        flag , mac_ip = VmInstance.delete_sys_disk_snap(snap_id=snap_id, user=user)
        self.vm_operation_log(request=request, operation_content=f'删除虚拟机系统快照, 云主机IP：{mac_ip}快照ID：{snap_id}',
                              remark='')
        return flag

    def modify_sys_snap_remarks(self, snap_id: int, remarks: str, request):
        """
        修改虚拟机系统盘快照备注信息

        :param snap_id: 快照id
        :param remarks: 备注信息
        :param user: 用户
        :return:
            VmDiskSnap()    # success
        :raises: VmError
        """

        snap, mac_ip = VmInstance.modify_sys_snap_remarks(snap_id=snap_id, remarks=remarks, user=request.user)

        self.vm_operation_log(request=request, operation_content=f'修改云主机快照备注信息, 备注信息为：{remarks} 云主机IP：{mac_ip} 快照ID：{snap_id}',
                              remark='')
        return snap

    def vm_rollback_to_snap(self, vm_uuid: str, snap_id: int, request, user):
        """
        回滚虚拟机系统盘到指定快照

        :param vm_uuid: 虚拟机id
        :param snap_id: 快照id
        :param user: 用户
        :return:
           True    # success

        :raises: VmError
        """
        vm = self._get_user_perms_vm(
            vm_uuid=vm_uuid, user=user, related_fields=(),
            allow_superuser=True, allow_resource=True, allow_owner=True
        )

        self.vm_operation_log(request=request, operation_content=f'云主机系统盘回滚到指定快照, 指定快照id为：{snap_id} 云主机IP：{vm.mac_ip}',
                              remark='')
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

        status_bool = vm_normal_status(vm=vm)
        if status_bool is False:
            raise errors.VmAccessDeniedError(msg='虚拟机搁置状态， 拒绝此操作')

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
        return VmInstance(vm=vm).mount_pci_device(device=device), vm

    def change_sys_disk(self, vm_uuid: str, image_id: int, request, user):
        """
        更换虚拟机系统镜像

        :param vm_uuid: 虚拟机uuid
        :param image_id: 系统镜像id
        :param user: 用户
        :return:
            Vm()   # success

        :raises: VmError
        """
        vm = self._get_user_perms_vm(
            vm_uuid=vm_uuid, user=user, related_fields=('user', 'host__group', 'image__ceph_pool__ceph'),
            allow_superuser=True, allow_resource=True, allow_owner=False
        )

        self.vm_operation_log(request=request, operation_content=f'更换云主机系统成功, 云主机IP：{vm.mac_ip}',
                              remark='')

        new_image = VmBuilder().get_image(image_id)  # 镜像
        return VmInstance(vm=vm).change_sys_disk(image=new_image)

    def migrate_vm(self, vm_uuid: str, host_id: int, request, force: bool = False):
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
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=request.user, related_fields=(
            'user', 'host__group', 'image__ceph_pool__ceph'))

        new_vm = VmInstance(vm=vm).migrate(host_id=host_id, force=force)
        HostManager.update_host_quota(host_id=vm.host_id)
        HostManager.update_host_quota(host_id=new_vm.host_id)

        self.vm_operation_log(request=request, operation_content=f'静态迁移云主机到指定宿主机, 云主机IP：{vm.mac_ip}，指定宿主机IP：{new_vm.host.ipv4}',
                              remark='')
        return new_vm

    # def reset_sys_disk(self, vm_uuid: str, user):
    #     """
    #     重置虚拟机系统盘，恢复到创建时状态
    #
    #     :param vm_uuid: 虚拟机uuid
    #     :param user: 用户
    #     :return:
    #         Vm()   # success
    #
    #     :raises: VmError
    #     """
    #     vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=(
    #         'user', 'host__group', 'image__ceph_pool__ceph'))
    #     return VmInstance(vm=vm).reset_sys_disk()

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

    def vm_miss_fix(self, vm_uuid: str, request):
        """
        宿主机上虚拟机丢失修复

        :param vm_uuid: 虚拟机uuid
        :param user: 用户
        :return:
            Vm()   # success

        :raises: VmError
        """
        vm = self._get_user_perms_vm(
            vm_uuid=vm_uuid, user=request.user, related_fields=('host', 'user', 'image__ceph_pool__ceph'))

        self.vm_operation_log(request=request, operation_content=f'尝试恢复丢失的云主机, 云主机IP：{vm.mac_ip}',
                              remark='')
        return VmInstance(vm).miss_fix()

    def live_migrate_vm(self, vm_uuid: str, dest_host_id: int, request):
        """
        迁移虚拟机，迁移后强制更新源与目标Host资源分配信息

        :param vm_uuid: 虚拟机uuid
        :param dest_host_id: 目标宿主机id
        :param user: 用户
        :return:
            MigrateTask()   # success

        :raises: VmError
        """
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=request.user, related_fields=(
            'user', 'host__group', 'image__ceph_pool__ceph'))
        task = VmInstance(vm).live_migrate(dest_host_id=dest_host_id)
        # HostManager.update_host_quota(host_id=vm.host_id)
        # HostManager.update_host_quota(host_id=dest_host_id)
        self.vm_operation_log(request=request, operation_content=f'动态迁移云主机到指定宿主机, 云主机IP：{vm.mac_ip}，指定宿主机IP：{task.dst_host_ipv4}',
                              remark='')
        return task

    def get_vm_stats(self, vm_uuid: str, user):
        """
        查询vm内存，硬盘io，网络io等信息

        :raises: VmError
        """
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=('host',))
        return VmInstance(vm).get_stats()

    def vm_sys_disk_expand(self, vm_uuid: str, expand_size: int, request):
        """
        vm系统盘扩容，系统盘最大5Tb

        :param expand_size: 在原有大小基础上扩容大小， GB
        :return:    vm
        :raises: VmError
        """
        vm = self._get_user_perms_vm(
            vm_uuid=vm_uuid, user=request.user, related_fields=('image__ceph_pool__ceph',),
            allow_superuser=True, allow_resource=True, allow_owner=False
        )

        self.vm_operation_log(request=request, operation_content=f'云主机系统盘扩容, 云主机IP：{vm.mac_ip}, 扩容大小为{expand_size}GB',
                              remark='')
        return VmInstance(vm).sys_disk_expand(expand_size)

    def vm_unshelve(self, vm_uuid: str, group_id, host_id, mac_ip_id, request):
        """虚拟机搁置服务恢复"""
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=request.user, related_fields=('host', 'host__group', 'user'),
                                     flag=True)
        self.vm_operation_log(request=request, operation_content=f'云主机搁置恢复, 云主机IP：{vm.mac_ip}',
                              remark='')
        return VmInstance(vm).unshelve_vm(group_id=group_id, host_id=host_id, mac_ip_id=mac_ip_id, user=request.user)

    def vm_shelve(self, vm_uuid: str, request):
        """虚拟机搁置服务"""
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=request.user, related_fields=('host', 'host__group', 'user'))

        self.vm_operation_log(request=request, operation_content=f'云主机搁置, 云主机IP：{vm.mac_ip}',
                              remark='')
        return VmInstance(vm).shelve_vm()

    def vm_delshelve(self, vm_uuid: str, request):
        """搁置虚拟机删除"""

        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=request.user, related_fields=('user', 'last_ip', 'last_ip__vlan',
                                                                                 'last_ip__vlan__group',
                                                                                 'last_ip__vlan__group__center'), flag=True)
        self.vm_operation_log(request=request, operation_content=f'删除搁置云主机, 云主机IP：{vm.mac_ip}',
                              remark='')
        return VmInstance(vm).delshelve_vm()

    def attach_ip(self, vm_uuid: str, request, mac_ip_obj):

        if not mac_ip_obj:
            raise errors.BadRequestError(msg='无效的ip')

        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=request.user, related_fields=('user',))
        resq = VmInstance(vm).attach_ip_vm(mac_ip_obj=mac_ip_obj)
        if resq is False:
            AttachmentsIPManager().detach_ip_to_vm(attach_ip_obj=mac_ip_obj)

        self.vm_operation_log(request=request, operation_content=f'云主机附加IP, 云主机IP：{vm.mac_ip}, 附加IP：{mac_ip_obj.ipv4}',
                              remark='')
        return resq

    def detach_ip(self, vm_uuid: str, request, mac_ip_obj):

        if not mac_ip_obj:
            raise errors.BadRequestError(msg='无效的ip')

        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=request.user, related_fields=('user',))

        if vm.mac_ip.id == mac_ip_obj.id:
            raise errors.BadRequestError(msg='您不能移除主IP。')

        self.vm_operation_log(request=request, operation_content=f'云主机移除附加IP, 云主机IP：{vm.mac_ip}, 附加IP：{mac_ip_obj.ipv4}',
                              remark='')

        return VmInstance(vm).detach_ip_vm(mac_ip_obj=mac_ip_obj)

    def attach_ip_list(self, vm_uuid: str, user):
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=('user',))
        queryset = AttachmentsIPManager().get_attach_ip_list(vm_uuid=vm_uuid)
        return queryset

    def vm_user_release_image(self, vm, new_image_name, user, log_manager):
        image_id = vm.image_id
        vm_uuid = vm.get_uuid()

        # clone 之前的操作
        vm_manager = VmInstance(vm=vm)
        if vm_manager.vm_domain.is_running():
            raise errors.VmRunningError(msg='请关闭虚拟机。 如果有挂载设备，都需要卸载。')

        vd = vm.vdisks
        if vd:
            raise errors.VmError(msg='请先卸载云硬盘')

        pci_devs = vm.pci_devices
        if pci_devs:
            raise errors.VmError(msg='请先卸载本地资源(PCI)设备。')

        att_ip = vm.get_attach_ip()
        if att_ip:
            raise errors.VmError(msg='请先移除主机附加的IP')

        try:

            flatten_bool = VmBuilder().user_flatten_image(image_id=image_id, vm_uuid=vm_uuid,
                                                          new_image_name=new_image_name)
        except FunctionTimedOut as e:
            msg = f'发布镜像失败，详细情况 ==》 用户：{user} 镜像名称：{new_image_name} 失败原因：{str(e)}'
            log_manager.add_log(title=f'发布镜像失败:{new_image_name}', about=log_manager.about.ABOUT_NORMAL, text=msg)
            raise errors.VmError(msg=f'image release timeout. Please contact the administrator.')

        except Exception as e:
            msg = f'发布镜像失败，详细情况 ==》 用户：{user} 镜像名称：{new_image_name} 失败原因：{str(e)}'
            log_manager.add_log(title=f'发布镜像失败:{new_image_name}', about=log_manager.about.ABOUT_NORMAL, text=msg)
            raise e

        return flatten_bool

    def vm_operation_log(self, request, operation_content, remark=''):
        user_operation_record.add_log(request=request, operation_content=operation_content, remark=remark)

    def vm_hand_over_user(self, vm_uuid: str, owner):
        vm = self._get_user_perms_vm(
            vm_uuid=vm_uuid, user=None, related_fields=('user',), query_user=False)
        vm.user = owner
        vm.save(update_fields=['user'])
        return vm
