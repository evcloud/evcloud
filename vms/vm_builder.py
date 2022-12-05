import uuid

from ceph.managers import RadosError, ImageExistsError
from compute.managers import CenterManager, GroupManager, HostManager, ComputeError
from image.managers import ImageManager, ImageError
from image.models import Image
from network.managers import VlanManager, MacIPManager, NetworkError
from utils.ev_libvirt.virt import (
    VirtError, VmDomain, VirtHost
)
from .models import Vm
from utils import errors
from .scheduler import HostMacIPScheduler
from .manager import VmManager
from .xml_builder import VmXMLBuilder


def get_vm_domain(vm: Vm):
    return VmDomain(host_ip=vm.host.ipv4, vm_uuid=vm.get_uuid())


class VmBuilder:
    """
    虚拟机创建
    """
    def __init__(self):
        self._center_manager = CenterManager()
        self._group_manager = GroupManager()
        self._host_manager = HostManager()
        self._vm_manager = VmManager()
        self._image_manager = ImageManager()
        self._vlan_manager = VlanManager()
        self._macip_manager = MacIPManager()

    @staticmethod
    def new_uuid_obj():
        """
        生成一个新的uuid字符串
        :return: uuid:str
        """
        return uuid.uuid4()

    def get_image(self, image_id: int):
        """
        获取image

        :return:
            Image()
            raise VmError

        :raise VmError
        """
        try:
            image = self._image_manager.get_image_by_id(image_id, related_fields=('ceph_pool__ceph', 'xml_tpl'))
        except ImageError as e:
            raise errors.VmError(err=e)
        if not image:
            raise errors.VmError(msg='镜像ID参数有误，未找到指定系统镜像')
        if not image.enable:
            raise errors.VmError(msg='镜像ID参数有误，镜像未启用')

        return image

    def get_vlan(self, vlan_id: int):
        """
           获取子网vlan

           :return:
               Vlan()
               raise VmError

           :raise VmError
           """
        try:
            vlan = self._vlan_manager.get_vlan_by_id(vlan_id)
        except NetworkError as e:
            raise errors.VmError(err=e)

        if not vlan:
            raise errors.VmError(msg='子网ID有误，子网不存在')

        return vlan

    def available_macip(self, ipv4: str, user, ip_public=None):
        """
       指定mac ip是否空闲可用，是否满足网络类型, 是否有权限使用

       :return:
           MacIP()          # 可用
           raise VmError    # 不可用

       :raise VmError
       """
        try:
            mac_ip = self._macip_manager.get_macip_by_ipv4(ipv4=ipv4)
        except NetworkError as e:
            raise errors.VmError(err=e)

        if not mac_ip:
            raise errors.VmError(msg='mac ip不存在')

        if not mac_ip.can_used():
            raise errors.VmError(msg='mac ip已被分配使用')

        vlan = mac_ip.vlan
        if not vlan:
            raise errors.VmError(msg='mac ip未关联子网vlan，无法判断ip是公网或私网，用户是否有权限使用')

        if not vlan.group.user_has_perms(user=user):
            raise errors.GroupAccessDeniedError(msg='无权限使用指定的IP地址')

        if ip_public is None:       # 不指定ip类型
            return mac_ip

        if ip_public:  # 指定分配公网ip
            if not vlan.is_public():
                raise errors.VmError(msg='指定的IP地址不是公网ip')
        else:  # 指定分配私网ip
            if vlan.is_public():
                raise errors.VmError(msg='指定的IP地址不是私网ip')

        return mac_ip

    def get_groups_host_check_perms(self, center_id: int, group_id: int, host_id: int, user, vlan=None):
        """
        检查用户是否有宿主机组或宿主机访问权限，优先使用host_id

        :param center_id: 分中心ID
        :param group_id: 宿主机组ID
        :param host_id: 宿主机ID
        :param user: 用户
        :param vlan: 指定了vlan, 需要保证宿主机资源和vlan属于同一个宿主机组
        :return:
                [], Host()          # host_id有效时
                [Group()], None     # host_id无效，group_id有效时

        :raises: VmError
        """
        if host_id:
            try:
                host = self._host_manager.get_host_by_id(host_id)
            except ComputeError as e:
                raise errors.VmError(msg=str(e))

            if not host:
                raise errors.VmError(msg='指定宿主机不存在')
            # 用户访问宿主机权限检查
            if not host.user_has_perms(user=user):
                raise errors.VmError(msg='当前用户没有指定宿主机的访问权限')

            if vlan and host.group_id != vlan.group_id:  # 指定vlan，是否同属于一个宿主机组
                raise errors.AcrossGroupConflictError(msg='指定的宿主机和指定的ip或vlan不在同一个宿主机组内')

            return [], host

        if group_id:
            if vlan and group_id != vlan.group_id:  # 指定vlan，是否同属于一个宿主机组
                raise errors.AcrossGroupConflictError(msg='指定的宿主机组和指定的ip或vlan不在同一个宿主机组内')

            try:
                group = self._group_manager.get_group_by_id(group_id=group_id)
            except ComputeError as e:
                raise errors.VmError(msg=f'查询宿主机组，{str(e)}')
            if not group:
                raise errors.VmError(msg='指定宿主机组不存在')

            # 用户访问宿主机组权限检查
            if not group.user_has_perms(user=user):
                raise errors.VmError(msg='当前用户没有指定宿主机的访问权限')

            return [group], None

        if center_id:
            if vlan:
                group = vlan.group
                if group.center_id != center_id:
                    raise errors.AcrossGroupConflictError(msg='指定的ip或vlan不属于指定的分中心')

                return [group], None

            try:
                groups = self._center_manager.get_user_group_queryset_by_center(center_or_id=center_id, user=user)
                groups = list(groups)
            except Exception as e:
                raise errors.VmError(msg=f'查询指定分中心下的宿主机组错误，{str(e)}')

            return groups, None

        raise errors.VmError(msg='必须指定一个有效的center id或者group id或者host id')

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
        :param sys_disk_size: 系统盘大小GB, 系统盘最大5Tb
        :return:
            Vm()
            raise VmError

        :raise VmError
        """
        macip = None  # 申请的macip
        vlan = None
        diskname = None  # clone的系统镜像

        if vcpu <= 0:
            raise errors.VmError.from_error(errors.BadRequestError(msg='无法创建虚拟机,vcpu参数无效'))
        if mem <= 0:
            raise errors.VmError.from_error(errors.BadRequestError(msg='无法创建虚拟机,men参数无效'))
        if not ((center_id and center_id > 0) or (group_id and group_id > 0) or (host_id and host_id > 0)):
            raise errors.VmError.from_error(errors.BadRequestError(
                msg='无法创建虚拟机,必须指定一个有效center_id或group_id或host_id参数'))

        if sys_disk_size and sys_disk_size > 5 * 1024:
            raise errors.VmError(msg='系统盘容量不得大于5TB')

        image = self.get_image(image_id)  # 镜像
        try:
            image_size = image.get_size()
        except Exception as e:
            raise errors.VmError(msg=f'获取系统镜像大小错误，{str(e)}')

        if sys_disk_size and sys_disk_size < image_size:
            raise errors.VmSysDiskSizeSmallError(msg='系统盘大小不得小于系统镜像大小')

        vm_uuid_obj = self.new_uuid_obj()
        vm_uuid = vm_uuid_obj.hex

        ceph_pool = image.ceph_pool
        data_pool = ceph_pool.data_pool if ceph_pool.has_data_pool else None
        try:
            rbd_manager = image.get_rbd_manager()
        except Exception as e:
            raise errors.VmError(msg=str(e))

        # 如果指定了vlan或ip
        if ipv4:
            macip = self.available_macip(ipv4=ipv4, user=user, ip_public=ip_public)  # ip是否可用
            groups, host_or_none = self.get_groups_host_check_perms(
                center_id=center_id, group_id=group_id, host_id=host_id, user=user, vlan=macip.vlan)
            macip = self._macip_manager.apply_for_free_ip(ipv4=ipv4)  # 分配ip
            if not macip:
                raise errors.VmError.from_error(errors.MacIpApplyFailed(msg='指定的IP地址不可用，不存在或已被占用'))
            vlan = macip.vlan
        elif vlan_id and vlan_id > 0:
            vlan = self.get_vlan(vlan_id)  # 局域子网
            if not vlan.group.user_has_perms(user=user):
                raise errors.GroupAccessDeniedError(msg='无权限使用指定的vlan资源')

            groups, host_or_none = self.get_groups_host_check_perms(
                center_id=center_id, group_id=group_id, host_id=host_id, user=user, vlan=vlan)
        else:
            groups, host_or_none = self.get_groups_host_check_perms(
                center_id=center_id, group_id=group_id, host_id=host_id, user=user)

        host = None  # 指示是否分配了宿主机和资源，指示创建失败时释放资源
        try:
            # 向宿主机申请资源
            scheduler = HostMacIPScheduler()
            try:
                if macip:
                    host, _ = scheduler.schedule(vcpu=vcpu, mem=mem, groups=groups, host=host_or_none, vlan=vlan,
                                                 need_mac_ip=False, ip_public=ip_public)
                else:
                    host, macip = scheduler.schedule(vcpu=vcpu, mem=mem, groups=groups, host=host_or_none,
                                                     vlan=vlan, ip_public=ip_public)
            except errors.ScheduleError as e:
                e.msg = f'申请资源错误,{str(e)}'
                raise errors.VmError.from_error(e)
            if not macip:
                raise errors.VmError.from_error(errors.MacIpApplyFailed(msg='申请mac ip失败'))

            # 创建虚拟机的系统镜像disk
            try:
                rbd_manager.clone_image(snap_image_name=image.base_image, snap_name=image.snap,
                                        new_image_name=vm_uuid, data_pool=data_pool)
                diskname = vm_uuid
            except RadosError as e:
                raise errors.VmError(msg=f'clone image error, {str(e)}')

            if sys_disk_size and sys_disk_size > image_size:
                if rbd_manager.resize_rbd_image(image_name=diskname, size=sys_disk_size * 1024 ** 3) is not True:
                    raise errors.VmError(msg=f'resize system disk size error')
            else:
                sys_disk_size = image_size

            # 创建虚拟机
            vm = self._create_vm2(vm_uuid=vm_uuid, diskname=diskname, vcpu=vcpu, mem=mem, image=image,
                                  host=host, macip=macip, user=user, remarks=remarks, sys_disk_size=sys_disk_size)
        except Exception as e:
            if macip:
                self._macip_manager.free_used_ip(ip_id=macip.id)  # 释放已申请的mac ip资源
            if host:
                self._host_manager.free_to_host(host_id=host.id, vcpu=vcpu, mem=mem)  # 释放已申请的宿主机资源
            if diskname:
                try:
                    rbd_manager.remove_image(image_name=diskname)
                except RadosError:
                    pass

            raise errors.VmError(msg=str(e))

        host.vm_created_num_add_1()  # 宿主机已创建虚拟机数量+1
        try:
            vm.update_sys_disk_size()  # 系统盘有变化，更新系统盘大小
        except Exception as e:
            pass

        return vm

    def create_vm_for_image(self, image_id: int, vcpu: int, mem: int, host_id=None, ipv4=None):
        """
        创建一个镜像虚拟机

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
        if vcpu <= 0:
            raise errors.VmError.from_error(errors.BadRequestError(msg='无法创建虚拟机,vcpu参数无效'))
        if mem <= 0:
            raise errors.VmError.from_error(errors.BadRequestError(msg='无法创建虚拟机,men参数无效'))
        if not (host_id and host_id > 0):
            raise errors.VmError.from_error(errors.BadRequestError(msg='无法创建虚拟机,必须指定一个有效host_id参数'))

        # 申请资源
        try:
            host = self._host_manager.claim_from_host(host_id=host_id, vcpu=vcpu, mem=mem)
            macip = MacIPManager.get_macip_by_ipv4(ipv4)
        except ComputeError as e:
            raise errors.ScheduleError.from_error(e)

        # 创建虚拟机
        try:
            try:
                # 构造虚拟机xml
                image = self.get_image(image_id)  # 镜像
                diskname = image.base_image
                vm_uuid = self.new_uuid_obj().hex
                xml_desc = VmXMLBuilder().build_vm_xml_desc(vm_uuid=vm_uuid, mem=mem, vcpu=vcpu,
                                                            vm_disk_name=diskname,
                                                            image=image, mac_ip=macip, is_image_vm=True)
            except Exception as e:
                raise errors.VmError(msg=f'构建镜像虚拟机xml错误,{str(e)}')

            try:
                # 保存元数据
                vm = Vm(uuid=vm_uuid, name=vm_uuid, vcpu=vcpu, mem=mem, disk=diskname,
                        host=host, mac_ip=macip, xml=xml_desc, image=image)
                image.vm_uuid = vm_uuid
                image.vm_mem = mem
                image.vm_vcpu = vcpu
                image.vm_host = host
                image.vm_mac_ip = macip
                image.save(update_fields=['vm_uuid', 'vm_mem', 'vm_vcpu', 'vm_host', 'vm_mac_ip'])
            except Exception as e:
                raise errors.VmError(msg=f'创建镜像虚拟机元数据错误,{str(e)}')

            try:
                # 创建虚拟机
                VirtHost(host_ipv4=host.ipv4).define(xml_desc=xml_desc)
            except VirtError as e:
                image.vm_uuid = None
                image.vm_mem = None
                image.vm_vcpu = None
                image.vm_host = None
                image.vm_mac_ip = None
                image.save()
                raise errors.VmError(msg=str(e))
        except Exception as e:
            if macip:
                self._macip_manager.free_used_ip(ip_id=macip.id)  # 释放已申请的mac ip资源
            if host:
                self._host_manager.free_to_host(host_id=host.id, vcpu=vcpu, mem=mem)  # 释放已申请的宿主机资源
            raise errors.VmError(msg=str(e))
        host.vm_created_num_add_1()  # 宿主机已创建虚拟机数量+1
        return vm

    @staticmethod
    def _create_vm2(vm_uuid: str, diskname: str, vcpu: int, mem: int, image, host, macip, sys_disk_size: int,
                    user, remarks: str = ''):
        """
        仅创建虚拟机，不会清理传入的各种资源

        :param vm_uuid: 虚拟机uuid
        :param diskname: 系统盘uuid
        :param vcpu: cpu数
        :param mem: 内存大小
        :param host: 宿主机对象
        :param macip: mac ip对象
        :param sys_disk_size: 系统盘大小GB
        :param user: 用户对象
        :param remarks: 虚拟机备注信息
        :return:
            Vm()
            raise VmError

        :raises: VmError
        """
        # 虚拟机xml
        try:
            xml_desc = VmXMLBuilder().build_vm_xml_desc(vm_uuid=vm_uuid, mem=mem, vcpu=vcpu, vm_disk_name=diskname,
                                                        image=image, mac_ip=macip)
        except Exception as e:
            raise errors.VmError(msg=f'构建虚拟机xml错误,{str(e)}')

        try:
            # 创建虚拟机元数据
            vm = Vm(uuid=vm_uuid, name=vm_uuid, vcpu=vcpu, mem=mem, disk=diskname, user=user,
                    remarks=remarks, host=host, mac_ip=macip, xml=xml_desc, image=image, sys_disk_size=sys_disk_size)
            vm.save()
        except Exception as e:
            raise errors.VmError(msg=f'创建虚拟机元数据错误,{str(e)}')

        # 创建虚拟机
        try:
            VirtHost(host_ipv4=host.ipv4).define(xml_desc=xml_desc)
        except VirtError as e:
            vm.delete()     # 删除虚拟机元数据
            raise errors.VmError(msg=str(e))

        return vm

    @staticmethod
    def reset_image_create_vm(vm: Vm, new_image: Image):
        """
        更换镜像创建虚拟机

        :param vm: Vm对象
        :param new_image: 新系统镜像 Image()
        :return:
            Vm()   # success

        :raises: VmError
        """
        try:
            vm_uuid = vm.uuid
            host = vm.host
            disk_name = vm.disk
            new_pool = new_image.ceph_pool
            new_data_pool = new_pool.data_pool if new_pool.has_data_pool else None
            old_vm_xml_desc = get_vm_domain(vm).xml_desc()

            # 虚拟机xml
            xml_desc = VmXMLBuilder().build_vm_xml_desc(
                vm_uuid=vm_uuid, mem=vm.mem, vcpu=vm.vcpu, vm_disk_name=disk_name, image=new_image, mac_ip=vm.mac_ip)
            rbd_manager = new_image.get_rbd_manager()
        except Exception as e:
            raise errors.VmError(msg=str(e))

        new_disk_ok = False
        vm_domain = None
        try:
            try:
                rbd_manager.clone_image(snap_image_name=new_image.base_image, snap_name=new_image.snap,
                                        new_image_name=disk_name, data_pool=new_data_pool)
            except ImageExistsError as e:
                pass
            new_disk_ok = True
            try:
                vm_domain = VmDomain.define(host_ipv4=host.ipv4, xml_desc=xml_desc)     # 新xml覆盖定义虚拟机
            except VirtError as e:
                raise errors.VmError(msg=str(e))

            vm.image = new_image
            vm.xml = xml_desc
            vm.disk_type = vm.DiskType.CEPH_RBD
            try:
                vm.save(update_fields=['image', 'xml', 'disk_type'])
            except Exception as e:
                raise errors.VmError(msg=f'更新虚拟机元数据失败, {str(e)}')
            return vm
        except Exception as e:
            if new_disk_ok:
                try:
                    rbd_manager.remove_image(image_name=disk_name)  # 删除新的系统盘image
                except RadosError:
                    pass
            if vm_domain is not None:
                try:
                    VmDomain.define(host_ipv4=host.ipv4, xml_desc=old_vm_xml_desc)  # 覆盖定义回原虚拟机
                except VirtError:
                    pass

            raise errors.VmError(msg=str(e))

    @staticmethod
    def migrate_create_vm(vm: Vm, new_host):
        """
        虚拟机迁移目标宿主机上创建虚拟机

        :param vm: Vm对象
        :param new_host: 目标宿主机Host()
        :return: (                  # success
            Vm(),
            begin_create: bool      # True：从新构建vm xml desc定义的vm，硬盘等设备需要重新挂载;
                                    # False：实时获取源vm xml desc, 原挂载的设备不受影响
        )

        :raises: VmError
        """
        vm_uuid = vm.uuid
        xml_desc = None
        begin_create = False  # vm xml不是从新构建的

        # 实时获取vm xml desc
        try:
            xml_desc = get_vm_domain(vm).xml_desc()
        except Exception as e:
            pass

        if not xml_desc:  # 实时获取vm xml, 从新构建虚拟机xml
            begin_create = True  # vm xml从新构建的
            try:
                xml_desc = VmXMLBuilder().build_vm_xml_desc(
                    vm_uuid=vm_uuid, mem=vm.mem, vcpu=vm.vcpu, vm_disk_name=vm.disk, image=vm.image, mac_ip=vm.mac_ip)
            except Exception as e:
                raise errors.VmError(msg=f'构建虚拟机xml错误，{str(e)}')

        new_vm_domain = None
        try:
            # 创建虚拟机
            try:
                new_vm_domain = VmDomain.define(host_ipv4=new_host.ipv4, xml_desc=xml_desc)
            except VirtError as e:
                raise errors.VmError(msg=str(e))

            vm.host = new_host
            vm.xml = xml_desc
            try:
                vm.save(update_fields=['host', 'xml'])
            except Exception as e:
                raise errors.VmError(msg=f'更新虚拟机元数据失败, {str(e)}')

            return vm, begin_create
        except Exception as e:
            # 目标宿主机删除虚拟机
            if new_vm_domain is not None:
                try:
                    new_vm_domain.undefine()
                except VirtError:
                    pass
            raise errors.VmError(msg=str(e))
