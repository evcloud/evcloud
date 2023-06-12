from ceph.managers import RadosError, ImageExistsError
from utils.ev_libvirt.virt import (
    VirtError, VmDomain, VirDomainNotExist, VirHostDown
)
from compute.managers import HostManager
from utils.vm_normal_status import vm_normal_status
from vdisk.manager import VdiskManager
from vdisk.models import Vdisk
from device.models import PCIDevice
from device.manager import PCIDeviceManager
from utils import errors
from .xml_builder import VmXMLBuilder
from .models import (
    Vm, VmDiskSnap, rename_sys_disk_delete, rename_image, Image
)
from .manager import VmArchiveManager, VmLogManager
from .migrate import VmMigrateManager
from .vm_builder import VmBuilder, get_vm_domain


class VmInstance:
    def __init__(self, vm: Vm):
        self.vm_uuid = vm.get_uuid()  # 提前暂存uuid, vm元数据删除后主键uuid会被设为None
        self._vm = vm
        self._vm_domain = None
        self._vdisk_manager = VdiskManager()
        self._pci_manager = PCIDeviceManager()
        self._host_manager = HostManager()

    @property
    def vm(self):
        return self._vm

    @property
    def vm_domain(self):
        if self._vm_domain is not None:
            if self._vm_domain.is_same_domain(self.vm.host.ipv4, vm_uuid=self.vm.get_uuid()):      # 排除vm迁移host变化
                return self._vm_domain

        self._vm_domain = get_vm_domain(self.vm)
        return self._vm_domain

    @classmethod
    def create_instance(cls, image_id: int, vcpu: int, mem: int, vlan_id: int, user, center_id=None, group_id=None,
                        host_id=None, ipv4=None, remarks=None, ip_public=None, sys_disk_size: int = None):
        """
        创建虚拟机

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
            VmInstance()
            raise VmError

        :raise VmError
        """
        vm = VmBuilder().create_vm(image_id=image_id, vcpu=vcpu, mem=mem, vlan_id=vlan_id, user=user,
                                   center_id=center_id, group_id=group_id, host_id=host_id, ipv4=ipv4,
                                   remarks=remarks, ip_public=ip_public, sys_disk_size=sys_disk_size)
        return cls(vm=vm)

    @classmethod
    def create_instance_for_image(cls, image_id: int, vcpu: int, mem: int, host_id=None, ipv4=None):
        """
        为镜像创建虚拟机

        说明：
            host_id不能为空，必须为127.0.0.1的宿主机，ipv4可以为镜像专用子网中的任意ip，可以重复使用；

        备注：虚拟机的名称和系统盘名称同虚拟机的uuid

        :param image_id: 镜像id
        :param vcpu: cpu数
        :param mem: 内存大小
        :param host_id: 宿主机id
        :param ipv4:  指定要创建的虚拟机ip
        :return:
            VmInstance()
            raise VmError

        :raise VmError
        """
        vm = VmBuilder().create_vm_for_image(image_id=image_id, vcpu=vcpu, mem=mem, host_id=host_id, ipv4=ipv4)
        return cls(vm=vm)

    def get_xml_desc(self):
        """
        动态从宿主机获取虚拟机的xml内容
        :return:
            xml: str    # success

        :raise VmError()
        """
        try:
            return self.vm_domain.xml_desc()
        except VirtError as e:
            raise errors.VmError(msg=str(e))

    def update_xml_from_domain(self):
        try:
            vm = self.vm
            xml_desc = self.get_xml_desc()
            vm.xml = xml_desc
            vm.save(update_fields=['xml'])
        except Exception:
            return False

        return True

    def mount_disk_to_domain(self, disk_xml: str):
        """
        向虚拟机挂载虚拟硬盘

        :param disk_xml: 硬盘xml
        :return:
            True    # success
            False   # failed
        :raises: VmError
        """
        try:
            if self.vm_domain.attach_device(xml=disk_xml):
                return True
            return False
        except VirtError as e:
            raise errors.VmError(msg=f'挂载硬盘错误，{str(e)}')

    def umount_disk_from_domain(self, disk_xml: str):
        """
        从虚拟机卸载虚拟硬盘

        :param disk_xml: 硬盘xml
        :return:
            True    # success
            False   # failed
        :raises: VmError
        """
        try:
            if self.vm_domain.detach_device(xml=disk_xml):
                return True
            return False
        except VirtError as e:
            raise errors.VmError(msg=f'卸载硬盘错误，{str(e)}')

    def modify_remark(self, remark: str):
        """
        修改虚拟机备注信息

        :param remark: 新的备注信息
        :return:
            True       # success
        :raise VmError()
        """
        self.vm.remarks = remark
        try:
            self.vm.save(update_fields=['remarks'])
        except Exception as e:
            raise errors.VmError(msg=f'更新备注信息失败, {str(e)}')

        return True

    def status(self):
        """
        获取虚拟机的运行状态

        :return:
            (state_code:int, state_str:str)     # success

        :raise VmError()
        """
        try:
            return self.vm_domain.status()
        except VirtError as e:
            raise errors.VmError(msg=f'获取虚拟机状态失败, {str(e)}')

    def _require_shutdown(self):
        """
        要求vm已关机状态
        :return: None
        :raises: VmError
        """
        try:
            run = self.vm_domain.is_running()
        except VirtError as e:
            raise errors.VmError(msg=f'获取虚拟机运行状态失败, {str(e)}', err=e)
        if run:
            raise errors.VmRunningError(msg='虚拟机正在运行，请先关闭虚拟机')

    def delete(self, force=False):
        """
        删除一个虚拟机

        :param force:   是否强制删除， 会强制关闭正在运行的虚拟机
        :return:
            True
            raise VmError

        :raise VmError
        """
        vm = self.vm
        host = vm.host
        # 虚拟机的状态
        domain = self.vm_domain

        try:
            run = domain.is_running()
        except VirDomainNotExist as e:
            run = False
        except VirHostDown as e:
            if not force:  # 非强制删除
                raise errors.VmError(msg='无法连接宿主机')
            run = False
        except VirtError as e:
            raise errors.VmError(msg=f'获取虚拟机运行状态失败, {str(e)}')

        if run:
            try:
                domain.poweroff()
            except VirtError as e:
                raise errors.VmRunningError(msg=f'关闭虚拟机失败，{str(e)}')

        # 删除系统盘快照
        try:
            snaps = vm.sys_disk_snaps.all()
            for snap in snaps:
                snap.delete()
        except Exception as e:
            raise errors.VmError(msg=f'删除虚拟机系统盘快照失败,{str(e)}')

        # 归档虚拟机
        try:
            vm_ahv = VmArchiveManager().add_vm_archive(vm)
        except errors.VmError as e:
            vm_ahv = VmArchiveManager().get_vm_archive(vm)
            if not vm_ahv:
                raise errors.VmError(msg=f'归档虚拟机失败，{str(e)}')

        log_manager = VmLogManager()

        # 删除虚拟机
        undefine_result = '已删除'
        try:
            if not domain.undefine():
                raise errors.VmError(msg='删除虚拟机失败')
        except VirHostDown:
            vm_ahv.set_host_not_release()
            undefine_result = '未删除'
        except (VirtError, errors.VmError):
            vm_ahv.delete()  # 删除归档记录
            raise errors.VmError(msg='删除虚拟机失败')

        # 删除虚拟机元数据
        vm_uuid = vm.get_uuid()     # 提前暂存uuid, vm元数据删除后主键uuid会被设为None
        try:
            vm.delete()
        except Exception as e:
            msg = f'虚拟机（uuid={vm_uuid}）{undefine_result}，并归档，但是虚拟机元数据删除失败;请手动删除虚拟机元数据。'
            log_manager.add_log(title='删除虚拟机元数据失败', about=log_manager.about.ABOUT_VM_METADATA, text=msg)
            raise errors.VmError(msg='删除虚拟机元数据失败')

        # 宿主机已创建虚拟机数量-1
        if not host.vm_created_num_sub_1():
            msg = f'虚拟机（uuid={vm_uuid}）{undefine_result}，并归档，宿主机（id={host.id}; ipv4={host.ipv4}）' \
                  f'已创建虚拟机数量-1失败, 请手动-1。'
            log_manager.add_log(title='宿主机已创建虚拟机数量-1失败',
                                about=log_manager.about.ABOUT_HOST_VM_CREATED, text=msg)

        # 释放mac ip
        mac_ip = vm.mac_ip
        if not mac_ip.set_free():
            msg = f'释放mac ip资源失败, 虚拟机uuid={vm_uuid};\n mac_ip信息：{mac_ip.get_detail_str()};\n ' \
                  f'请查看核对虚拟机是否已成功删除并归档，如果已删除请手动释放此mac_ip资源'
            log_manager.add_log(title='释放mac ip资源失败', about=log_manager.about.ABOUT_MAC_IP, text=msg)

        # 卸载所有挂载的虚拟硬盘
        try:
            self._vdisk_manager.umount_all_from_vm(vm_uuid=vm_uuid)
        except errors.VdiskError as e:
            msg = f'删除虚拟机时，卸载所有虚拟硬盘失败, 虚拟机uuid={vm_uuid};\n' \
                  f'请查看核对虚拟机是否已删除归档，请手动解除所有虚拟硬盘与虚拟机挂载关系'
            log_manager.add_log(title='删除虚拟机时，卸载所有虚拟硬盘失败', about=log_manager.about.ABOUT_VM_DISK, text=msg)

        # 释放宿主机资源
        if not host.free(vcpu=vm.vcpu, mem=vm.mem):
            msg = f'释放宿主机资源失败, 虚拟机uuid={vm_uuid};\n 宿主机信息：id={host.id}; ipv4={host.ipv4};\n' \
                  f'未释放资源：mem={vm.mem}MB;vcpu={vm.vcpu}；\n请查看核对虚拟机是否已成功删除并归档，如果已删除请手动释放此宿主机资源'
            log_manager.add_log(title='释放宿主机men, cpu资源失败', about=log_manager.about.ABOUT_MEM_CPU, text=msg)

        # vm系统盘RBD镜像修改了已删除归档的名称
        vm_ahv.rename_sys_disk_archive()
        return True

    def delete_for_image(self, force=False):
        """
        删除一个镜像虚拟机

        :param force:   是否强制删除， 会强制关闭正在运行的虚拟机
        :return:
            True
            raise VmError

        :raise VmError
        """
        # 虚拟机的状态
        domain = self.vm_domain
        vm = self.vm
        host = vm.host
        try:
            run = domain.is_running()
        except VirDomainNotExist as e:
            run = False
        except VirHostDown as e:
            if not force:  # 非强制删除
                raise errors.VmError(msg='无法连接宿主机')
            run = False
        except VirtError as e:
            raise errors.VmError(msg=f'获取虚拟机运行状态失败, {str(e)}')

        if run:
            try:
                domain.poweroff()
            except VirtError as e:
                raise errors.VmRunningError(msg=f'关闭虚拟机失败，{str(e)}')
        # 删除虚拟机
        undefine_result = '已删除'
        try:
            if not domain.undefine():
                raise errors.VmError(msg='删除虚拟机失败')
        except VirHostDown:
            undefine_result = '未删除'
        except (VirtError, errors.VmError):
            raise errors.VmError(msg='删除虚拟机失败')

        log_manager = VmLogManager()
        # 宿主机已创建虚拟机数量-1
        if not host.vm_created_num_sub_1():
            msg = f'镜像虚拟机（uuid={vm.get_uuid()}）{undefine_result}，宿主机（id={host.id}; ipv4={host.ipv4}）' \
                  f'已创建虚拟机数量-1失败, 请手动-1。'
            log_manager.add_log(title='镜像宿主机已创建虚拟机数量-1失败',
                                about=log_manager.about.ABOUT_HOST_VM_CREATED, text=msg)
        # 释放宿主机资源
        if not host.free(vcpu=vm.vcpu, mem=vm.mem):
            msg = f'释放镜像宿主机资源失败, 虚拟机uuid={vm.get_uuid()};\n 宿主机信息：id={host.id}; ipv4={host.ipv4};\n' \
                  f'未释放资源：mem={vm.mem}MB;vcpu={vm.vcpu}；\n请查看核对虚拟机是否已成功删除并归档，如果已删除请手动释放此宿主机资源'
            log_manager.add_log(title='释放镜像宿主机men, cpu资源失败', about=log_manager.about.ABOUT_MEM_CPU, text=msg)
        return True

    def edit_vcpu_mem(self, vcpu: int = 0, mem: int = 0,  force=False, update_vm=True):
        """
        修改虚拟机vcpu和内存大小

        :param vcpu:要修改的vcpu数，默认0 不修改
        :param mem: 要修改的内存大小，默认0 不修改
        :param force:   是否强制修改, 会强制关闭正在运行的虚拟机
        :param update_vm: 是否更新虚拟机元数据，对于镜像虚拟机不更新
        :return:
            True
            raise VmError

        :raise VmError
        """
        vm = self.vm
        if vcpu < 0 or mem < 0:
            raise errors.VmError.from_error(errors.BadRequestError(msg='vcpu或mem不能小于0'))

        if vcpu == 0 and mem == 0:
            return True

        # 没有变化直接返回
        if vm.vcpu == vcpu and vm.mem == mem:
            return True

        host = vm.host
        # 虚拟机的状态
        vm_domain = self.vm_domain
        try:
            run = vm_domain.is_running()
        except VirtError as exc:
            raise errors.VmError(msg='获取虚拟机运行状态失败' + str(exc))
        if run:
            if not force:
                raise errors.VmRunningError(msg='虚拟机正在运行，请先关闭虚拟机')
            try:
                vm_domain.poweroff()
            except VirtError as exc:
                raise errors.VmError(msg='强制关闭虚拟机失败')

        old_xml_desc = vm_domain.xml_desc()
        new_xml_desc = old_xml_desc

        cpu_delta = 0
        mem_delta = 0
        if vcpu > 0 and vcpu != vm.vcpu:
            cpu_delta = vcpu - vm.vcpu

        if mem > 0 and mem != vm.mem:
            mem_delta = mem - vm.mem

        if cpu_delta != 0:
            vm.vcpu = vcpu
            try:
                new_xml_desc = VmXMLBuilder.xml_edit_vcpu(xml_desc=new_xml_desc, vcpu=vcpu)
            except errors.VmError as e:
                raise e

        if mem_delta != 0:
            vm.mem = mem
            try:
                new_xml_desc = VmXMLBuilder.xml_edit_mem(xml_desc=new_xml_desc, mem=mem)
            except errors.VmError as e:
                raise e

        # 宿主机是否满足资源需求
        if cpu_delta > 0:
            if not host.meet_needs(vcpu=cpu_delta, mem=0, check_vm_limit=False):
                raise errors.VmError.from_error(errors.VcpuNotEnough(msg='宿主机已没有足够的vcpu资源'))

        if mem_delta > 0:
            if not host.meet_needs(vcpu=0, mem=mem_delta, check_vm_limit=False):
                raise errors.VmError.from_error(errors.RamNotEnough(msg='宿主机已没有足够的内存资源'))

        # 宿主机资源扣除或释放
        if not host.deduct_delta(cpu_delta=cpu_delta, mem_delta=mem_delta):
            raise errors.VmError(msg='扣除或释放宿主机vcpu或mem资源失败')

        # 创建虚拟机
        try:
            vm_domain = VmDomain.define(host_ipv4=host.ipv4, xml_desc=new_xml_desc)
        except VirtError as e:
            host.deduct_delta(cpu_delta=-cpu_delta, mem_delta=-mem_delta)   # 宿主机资源扣除或释放还原
            raise errors.VmError(msg='修改虚拟机失败')
        if update_vm:
            try:
                vm.xml = vm_domain.xml_desc()
                vm.save()
            except Exception as e:
                host.deduct_delta(cpu_delta=-cpu_delta, mem_delta=-mem_delta)  # 宿主机资源扣除或释放还原
                try:
                    vm_domain.host.define(xml_desc=old_xml_desc)
                except VirtError:
                    pass

                raise errors.VmError(msg=f'修改虚拟机元数据失败, {str(e)}')

        return True

    def operations(self, op: str):
        """
        操作虚拟机

        :param op: 操作，['start', 'reboot', 'shutdown', 'poweroff', 'delete', 'delete_force']
        :return:
            True    # success
            False   # failed
        :raise VmError
        """
        # 删除操作
        try:
            if op == 'delete':
                return self.delete()
            elif op == 'delete_force':
                return self.delete(force=True)
        except errors.VmError as e:
            raise e

        # 普通操作
        try:
            domain = self.vm_domain
            if op == 'start':
                return domain.start()
            elif op == 'reboot':
                return domain.reboot()
            elif op == 'shutdown':
                return domain.shutdown()
            elif op == 'poweroff':
                return domain.poweroff()
            else:
                raise errors.VmError.from_error(errors.BadRequestError(msg='无效的操作'))
        except VirtError as e:
            raise errors.VmError(msg=str(e))

    def mount_disk(self, vdisk: Vdisk):
        """
        向虚拟机挂载硬盘

        *虚拟机和硬盘需要在同一个分中心

        :param vdisk: 虚拟硬盘元数据实例
        :return:
            Vdisk()    # success

        :raises: VmError
        """
        vm = self.vm
        vdisk_uuid = vdisk.uuid
        host = vm.host
        if host.group.center_id != vdisk.quota.group.center_id:
            raise errors.AcrossCenterConflictError(msg='虚拟机和硬盘不在同一个分中心')

        xml_desc = self.vm_domain.xml_desc()
        disk_list, dev_list = VmXMLBuilder().get_vm_vdisk_dev_list(xml_desc=xml_desc)
        if vdisk_uuid in disk_list:
            return vdisk

        dev = VmXMLBuilder().new_vdisk_dev(dev_list)
        if not dev:
            raise errors.VmTooManyVdiskMounted()

        # 硬盘元数据和虚拟机建立挂载关系
        try:
            self._vdisk_manager.mount_to_vm(vdisk_uuid=vdisk_uuid, vm=vm, dev=dev)
        except errors.VdiskError as e:
            raise errors.VmError.from_error(e)

        # 向虚拟机挂载硬盘
        try:
            xml = vdisk.xml_desc(dev=dev)
            ok = self.mount_disk_to_domain(disk_xml=xml)
            if not ok:
                raise errors.VmError(msg='向虚拟机挂载硬盘失败')
        except (errors.VmError, Exception) as e:
            try:
                self._vdisk_manager.umount_from_vm(vdisk_uuid=vdisk_uuid)
            except errors.VdiskError:
                msg = f'硬盘与虚拟机解除挂载关系失败, 虚拟机uuid={vm.get_uuid()};\n' \
                      f'硬盘uuid={vdisk.uuid};\n 请查看核对此硬盘是否被挂载到此虚拟机，如果已挂载到此虚拟机，' \
                      f'请忽略此记录，如果未挂载，请手动解除与虚拟机挂载关系'
                log_manager = VmLogManager()
                log_manager.add_log(title='硬盘与虚拟机解除挂载关系失败', about=log_manager.about.ABOUT_VM_DISK, text=msg)

            raise errors.VmError.from_error(e)

        # 更新vm元数据中的xml
        self.update_xml_from_domain()
        return vdisk

    def umount_disk(self, vdisk: Vdisk):
        """
        从虚拟机卸载硬盘

        :param vdisk: 虚拟硬盘元数据实
        :return:
            Vdisk()    # success

        :raises: VmError
        """
        if self.vm.uuid != vdisk.vm.uuid:
            raise errors.VmError(msg='虚拟机和要卸载的硬盘不存在挂载关系')

        # 从虚拟机卸载硬盘
        xml = vdisk.xml_desc()
        try:
            ok = self.umount_disk_from_domain(disk_xml=xml)
            if not ok:
                raise errors.VmError(msg='从虚拟机卸载硬盘失败')
        except errors.VmError as e:
            raise e

        # 硬盘元数据和虚拟机解除挂载关系
        try:
            self._vdisk_manager.umount_from_vm(vdisk_uuid=vdisk.uuid)
        except errors.VdiskError as e:
            try:
                self.mount_disk_to_domain(disk_xml=xml)
            except errors.VmError:
                pass

            raise errors.VmError.from_error(e)

        # 更新vm元数据中的xml
        self.update_xml_from_domain()
        return vdisk

    def create_sys_snap(self, remarks: str):
        """
        创建虚拟机系统盘快照

        :param remarks: 快照备注信息
        :return:
            VmDiskSnap()    # success
        :raises: VmError
        """
        vm = self.vm
        if vm.disk_type == vm.DiskType.LOCAL:
            raise errors.VmError.from_error(
                errors.Unsupported(msg='虚拟主机为本地硬盘，不支持创建快照'))

        ceph_pool = vm.ceph_pool
        disk_snap = VmDiskSnap(disk=vm.disk, vm=vm, ceph_pool=ceph_pool, remarks=remarks)
        try:
            disk_snap.save()
        except Exception as e:
            raise errors.VmError(msg=str(e))

        return disk_snap

    def rollback_to_snap(self, snap_id: int):
        """
        回滚虚拟机系统盘到指定快照

        :param snap_id: 快照id
        :return:
           True    # success

        :raises: VmError
        """
        vm = self.vm
        if vm.disk_type == vm.DiskType.LOCAL:
            raise errors.VmError.from_error(
                errors.Unsupported(msg='虚拟主机为本地硬盘，不支持快照回滚'))

        self._require_shutdown()

        snap = VmDiskSnap.objects.select_related('ceph_pool', 'ceph_pool__ceph').filter(pk=snap_id).first()
        if not snap:
            raise errors.SnapNotExist(msg='快照不存在')

        if snap.disk != vm.disk:
            raise errors.SnapNotBelongToVm(msg='快照不属于此主机')

        try:
            rbd_mgr = snap.get_rbd_manager()
            rbd_mgr.image_rollback_to_snap(image_name=vm.disk, snap=snap.snap)
        except (RadosError, Exception) as e:
            raise errors.VmError(msg=str(e))

        try:
            vm.update_sys_disk_size()  # 系统盘有变化，更新系统盘大小
        except Exception as e:
            pass

        return True

    @staticmethod
    def get_user_disk_snap(snap_id: int, user):
        """
        获取用户有权限访问的系统盘快照

        :param snap_id: 快照id
        :param user: 用户
        :return:
            VmDiskSnap()
        :raises: VmError
        """
        snap = VmDiskSnap.objects.select_related('vm', 'vm__user').filter(pk=snap_id).first()
        if not snap:
            raise errors.VmError.from_error(errors.NotFoundError(msg='快照不存在'))

        if not user.is_superuser:
            if snap.vm and not snap.vm.user_has_perms(user):
                raise errors.VmError.from_error(errors.AccessDeniedError(msg='没有此快照的访问权限'))

        status_bool = vm_normal_status(vm=snap.vm)
        if status_bool is False:
            raise errors.VmAccessDeniedError(msg='云主机搁置状态， 拒绝此操作')

        return snap

    @staticmethod
    def delete_sys_disk_snap(snap_id: int, user):
        """
        删除虚拟机系统盘快照

        :param snap_id: 快照id
        :param user: 用户
        :return:
            True    # success

        :raises: VmError
        """
        snap = VmInstance.get_user_disk_snap(snap_id=snap_id, user=user)

        try:
            snap.delete()
        except Exception as e:
            raise errors.VmError(msg=str(e))

        return True

    @staticmethod
    def modify_sys_snap_remarks(snap_id: int, remarks: str, user):
        """
        修改虚拟机系统盘快照备注信息

        :param snap_id: 快照id
        :param remarks: 备注信息
        :param user: 用户
        :return:
            VmDiskSnap()    # success
        :raises: VmError
        """
        snap = VmInstance.get_user_disk_snap(snap_id=snap_id, user=user)

        try:
            snap.remarks = remarks
            snap.save(update_fields=['remarks'])
        except Exception as e:
            raise errors.VmError(msg=str(e))

        return snap

    def umount_pci_device(self, device: PCIDevice):
        """
        从虚拟机卸载pci设备

        :param device: pci设备
        :return:
            PCIDevice()    # success

        :raises: VmError
        """
        self._require_shutdown()
        # 卸载设备
        try:
            self._pci_manager.umount_from_vm(device=device)
        except errors.DeviceError as e:
            raise errors.VmError.from_error(e)

        # 更新vm元数据中的xml
        self.update_xml_from_domain()
        return device

    def mount_pci_device(self, device: PCIDevice):
        """
        向虚拟机挂载pci设备

        :param device: pci设备
        :return:
            PCIDevice()   # success

        :raises: VmError
        """
        self._require_shutdown()
        # 向虚拟机挂载
        try:
            self._pci_manager.mount_to_vm(vm=self.vm, device=device)
        except errors.DeviceError as e:
            raise errors.VmError.from_error(e)

        # 更新vm元数据中的xml
        self.update_xml_from_domain()
        return device

    # def reset_sys_disk(self):
    #     """
    #     重置虚拟机系统盘，恢复到创建时状态
    #
    #     :return:
    #         Vm()   # success
    #
    #     :raises: VmError
    #     """
    #     # 删除快照记录
    #     self._require_shutdown()
    #     vm = self.vm
    #     try:
    #         vm.sys_snaps.delete()
    #     except Exception as e:
    #         raise errors.VmError(msg=f'删除虚拟机系统盘快照失败，{str(e)}')
    #
    #     disk_name = vm.disk
    #     ceph_pool = vm.ceph_pool
    #     pool_name = ceph_pool.pool_name
    #     ceph = ceph_pool.ceph
    #     image = vm.image
    #     data_pool = ceph_pool.data_pool if ceph_pool.has_data_pool else None
    #
    #     ok, deleted_disk = rename_sys_disk_delete(ceph=ceph, pool_name=pool_name, disk_name=disk_name)
    #     if not ok:
    #         raise errors.VmError(msg='虚拟机系统盘重命名失败')
    #
    #     rbd_manager = image.get_rbd_manager()
    #     try:
    #         rbd_manager.clone_image(snap_image_name=image.base_image, snap_name=image.snap,
    #                                 new_image_name=disk_name, data_pool=data_pool)
    #     except (RadosError, ImageExistsError) as e:
    #         # 原系统盘改回原名
    #         try:
    #             rename_image(ceph=ceph, pool_name=pool_name, image_name=deleted_disk, new_name=disk_name)
    #         except Exception as exc:
    #             pass
    #         raise errors.VmError(msg=f'虚拟机系统盘创建失败, {str(e)}')
    #
    #     try:
    #         vm.update_sys_disk_size()  # 系统盘有变化，更新系统盘大小
    #     except Exception as e:
    #         pass
    #
    #     return vm

    def change_sys_disk(self, image):
        """
        更换虚拟机系统镜像

        :param image: 系统镜像
        :return:
            Vm()   # success

        :raises: VmError
        """
        vm = self.vm
        new_image = image  # 镜像
        # 同一个iamge
        # if new_image.pk == vm.image.pk:
        #     return self.reset_sys_disk()

        # vm和image是否在同一个分中心
        host = vm.host
        if host.group.center_id != new_image.ceph_pool.ceph.center_id:
            raise errors.AcrossCenterConflictError(msg='虚拟机和系统镜像不在同一个分中心')

        self._require_shutdown()

        # 删除快照记录
        try:
            vm.sys_snaps.delete()
        except Exception as e:
            raise errors.VmError(msg=f'删除虚拟机系统盘快照失败，{str(e)}')

        # rename sys disk
        disk_name = vm.disk
        old_pool = vm.ceph_pool
        old_pool_name = old_pool.pool_name
        old_ceph = old_pool.ceph
        ok, deleted_disk = rename_sys_disk_delete(ceph=old_ceph, pool_name=old_pool_name, disk_name=disk_name)
        if not ok:
            raise errors.VmError(msg='虚拟机系统盘重命名失败')

        try:
            vm = VmBuilder.reset_image_create_vm(vm=self.vm, new_image=new_image)
        except errors.VmError as e:
            # 原系统盘改回原名
            try:
                rename_image(ceph=old_ceph, pool_name=old_pool_name, image_name=deleted_disk, new_name=disk_name)
            except Exception as exc:
                pass
            raise errors.VmError(msg=str(e))

        # 向虚拟机挂载硬盘
        for vdisk in vm.vdisks:
            vdisk_xml = vdisk.xml_desc(dev=vdisk.dev)
            try:
                self.mount_disk_to_domain(disk_xml=vdisk_xml)
            except errors.VmError as e:
                self._vdisk_manager.umount_from_vm(vdisk_uuid=vdisk.uuid)

        # PCI设备
        for dev in vm.pci_devices:
            try:
                self._pci_manager.mount_to_vm(vm=vm, device=dev)
            except errors.DeviceError as e:
                raise errors.VmError(msg=str(e))

        # 更新vm元数据中的xml
        self.update_xml_from_domain()

        try:
            vm.update_sys_disk_size()   # 系统盘有变化，更新系统盘大小
        except Exception as e:
            pass

        return vm

    def change_password(self, username: str, password: str):
        """
        重置虚拟机系统登录密码

        :param username: 用户名
        :param password: 新密码
        :return:
            Vm()   # success

        :raises: VmError
        """
        vm = self.vm
        if vm.sys_type not in [Image.SYS_TYPE_LINUX, Image.SYS_TYPE_UNIX]:
            raise errors.VmError(msg=f'只支持linux或unix系统虚拟主机修改密码')

        # 虚拟机的状态
        try:
            run = self.vm_domain.is_running()
        except VirtError as e:
            raise errors.VmError(msg=f'获取虚拟机运行状态失败,{str(e)}')
        if not run:
            raise errors.VmError(msg='虚拟机没有运行')

        try:
            ok = self.vm_domain.set_user_password(username=username, password=password)
        except VirtError as e:
            raise errors.VmError(msg=f'修改密码失败，{str(e)}')

        if not ok:
            raise errors.VmError(msg='修改密码失败')

        try:
            vm.init_password = password
            vm.save(update_fields=['init_password'])
        except Exception:
            pass
        return vm

    def migrate(self, host_id: int, force: bool = False):
        """
        迁移虚拟机

        :param host_id: 宿主机id
        :param force: True(强制迁移)，False(普通迁移)
        :return:
            Vm()   # success

        :raises: VmError
        """
        vm = self.vm
        return VmMigrateManager().static_migrate(vm=vm, host_id=host_id, force=force)

    def miss_fix(self):
        """
        宿主机上虚拟机丢失修复

        :return:
            Vm()   # success

        :raises: VmError
        """
        vm = self.vm
        if vm.disk_type == vm.DiskType.LOCAL:
            raise errors.VmError.from_error(
                errors.Unsupported(msg='虚拟主机为本地硬盘，暂不支持丢失修复'))

        host = vm.host
        # 虚拟机
        domain = self.vm_domain
        try:
            ok = domain.exists()
        except VirHostDown as e:
            raise errors.VmError(msg=f'无法连接宿主机', err_code='HostDown')
        except VirtError as e:
            raise errors.VmError(msg=f'确认宿主机上是否丢失虚拟机时错误, {str(e)}')
        if ok:
            raise errors.VmAlreadyExistError(msg='虚拟主机未丢失, 无需修复')

        # disk rbd是否存在
        disk_name = vm.disk
        try:
            rbd_mgr = vm.get_rbd_manager()
            ok = rbd_mgr.image_exists(image_name=disk_name)
        except Exception as e:
            raise errors.VmError(msg=f'查询虚拟主机系统盘镜像时错误，{str(e)}')

        if not ok:
            raise errors.VmDiskImageMissError(msg=f'虚拟主机系统盘镜像不存在，无法恢复此虚拟主机')

        try:
            xml_desc = VmXMLBuilder().build_vm_xml_desc(
                vm_uuid=vm.get_uuid(), mem=vm.mem, vcpu=vm.vcpu, vm_disk_name=disk_name,
                image_xml_tpl=vm.image_xml_tpl, ceph_pool=vm.ceph_pool, mac_ip=vm.mac_ip)
        except Exception as e:
            raise errors.VmError(msg=f'构建虚拟主机xml错误，{str(e)}')

        # 创建虚拟机
        try:
            VmDomain.define(host_ipv4=host.ipv4, xml_desc=xml_desc)
        except VirtError as e:
            raise errors.VmError(msg=f'宿主机上创建虚拟主机错误，{str(e)}')

        # 向虚拟机挂载硬盘
        for vdisk in vm.vdisks:
            try:
                xml = vdisk.xml_desc(dev=vdisk.dev)
                self.mount_disk_to_domain(disk_xml=xml)
            except (errors.VmError, Exception) as e:
                # vdisk和vm元数据挂载关系解除失败
                try:
                    self._vdisk_manager.umount_from_vm(vdisk_uuid=vdisk.uuid)
                except errors.VdiskError as e2:
                    pass

        return vm

    def live_migrate(self, dest_host_id: int):
        """
        动态迁移虚拟机

        :param dest_host_id: 目标宿主机id
        :return:
            MigrateTask()   # success

        :raises: VmError
        """
        return VmMigrateManager().live_migrate_vm(vm=self.vm, dest_host_id=dest_host_id)

    def get_stats(self):
        """
        查询vm内存，硬盘io，网络io等信息

        :raises: VmError
        """
        try:
            stats = self.vm_domain.get_stats()
        except VirtError as exc:
            raise errors.VmError.from_error(exc)

        return stats.to_dict()

    def sys_disk_expand(self, expand_size: int):
        """
        vm系统盘扩容，系统盘最大5Tb

        :param expand_size: 在原有大小基础上扩容大小， GB
        :return:    vm
        :raises: VmError
        """
        vm = self.vm
        if vm.disk_type != vm.DiskType.CEPH_RBD:
            raise errors.Unsupported(msg='只支持CEPH RBD硬盘扩容，不支持宿主机本地硬盘')

        self._require_shutdown()

        gb = 1024 ** 3
        old_size_bytes = vm.get_sys_disk_size() * gb
        if old_size_bytes == 0:
            raise errors.VmError(msg='查询系统盘大小失败')

        new_size_bytes = old_size_bytes + expand_size * gb
        if new_size_bytes > 5 * 1024 * gb:      # 5Tb
            raise errors.Unsupported(msg='系统盘大小不允许超过5Tb')

        try:
            rbd = vm.get_rbd_manager()
            ok = rbd.resize_rbd_image(image_name=vm.disk, size=new_size_bytes)
        except Exception as e:
            raise errors.VmError(msg=f'修改系统盘大小错误，{str(e)}')

        if ok:
            vm.update_sys_disk_size()
            return vm

        raise errors.VmError(msg='修改系统盘大小失败')

    def shelve_vm(self):
        """搁置虚拟机
            1. 本地硬盘不支持搁置
            2. 除GPU、网卡的其他PCI设备不支持搁置
        """
        vm = self.vm
        vm_uuid = vm.get_uuid()
        if self.vm_domain.is_running():
            raise errors.VmRunningError(msg='请关闭虚拟机')

        if vm.disk_type == vm.DiskType.LOCAL:
            raise errors.VmError.from_error(
                errors.Unsupported(msg='虚拟主机硬盘为本地硬盘，不支持搁置服务。'))

        pci_devs = vm.pci_devices
        pci_objs = pci_devs.exclude(type=PCIDevice.TYPE_GPU).exclude(type=PCIDevice.TYPE_ETH)
        if pci_objs:
            raise errors.VmError(msg='请先卸载PCI设备。')

        for device in pci_devs:
            try:
                device.umount()
            except errors.DeviceError as e:
                raise errors.VmError(msg=f'卸载主机挂载的PCI设备失败, {str(e)}')

        log_manager = VmLogManager()

        # 删除虚拟机
        try:
            if not self.vm_domain.undefine():
                raise errors.VmError(msg='删除虚拟机失败')
        except VirHostDown:
            raise errors.VmError(msg='搁置服务失败。')
        except (VirtError, errors.VmError):
            raise errors.VmError(msg='删除虚拟机失败')

        macip = vm.mac_ip
        if not macip.set_free():
            msg = f'释放mac ip资源失败, 虚拟机uuid={vm_uuid};\n mac_ip信息：{macip.get_detail_str()};\n ' \
                  f'如果已删除虚拟机请手动释放此mac_ip资源'
            log_manager.add_log(title='释放mac ip资源失败', about=log_manager.about.ABOUT_MAC_IP, text=msg)
            raise errors.VmError(msg=msg)

        # 释放宿主机资源
        if not vm.host.free(vcpu=vm.vcpu, mem=vm.mem):
            msg = f'释放宿主机资源失败, 虚拟机uuid={vm_uuid};\n 宿主机信息：id={vm.host.id}; ipv4={vm.host.ipv4};\n' \
                  f'未释放资源：mem={vm.mem}MB;vcpu={vm.vcpu}'
            raise errors.VmError(msg=msg)

        # 宿主机已创建虚拟机数量-1
        if not vm.host.vm_created_num_sub_1():
            msg = f'镜像虚拟机（uuid={vm_uuid}），宿主机（id={vm.host.id}; ipv4={vm.host.ipv4}）' \
                  f'已创建虚拟机数量-1失败, 请手动-1。'
            log_manager.add_log(title='镜像宿主机已创建虚拟机数量-1失败',
                                about=log_manager.about.ABOUT_HOST_VM_CREATED, text=msg)
            raise errors.VmError(msg=msg)

        vm.mac_ip = None
        vm.host = None
        vm.vm_status = vm.VmStatus.SHELVE.value
        vm.last_ip = macip
        vm.center = macip.vlan.group.center
        vm.save(update_fields=['mac_ip', 'host', 'vm_status', 'last_ip', 'center'])
        return True

    def unshelve_vm(self, group_id, host_id, mac_ip_id, user):
        """恢复搁置的虚拟机"""
        vm = self.vm
        return VmBuilder().unshelve_create_vm(vm=vm, group_id=group_id, host_id=host_id,
                                              mac_ip_id=mac_ip_id, user=user)

