import uuid
import subprocess

from django.db.models import Q

from ceph.managers import RadosError, get_rbd_manager, ImageExistsError
from ceph.models import CephCluster
from compute.managers import CenterManager, GroupManager, HostManager, ComputeError
from image.managers import ImageManager, ImageError
from network.managers import VlanManager, MacIPManager, NetworkError
from vdisk.manager import VdiskManager, VdiskError
from device.manager import DeviceError, PCIDeviceManager
from utils.ev_libvirt.virt import VirtAPI, VirtError, VmDomain, VirDomainNotExist, VirHostDown
from .models import (Vm, VmArchive, VmLog, VmDiskSnap, rename_sys_disk_delete, rename_image, MigrateLog, Flavor)
from .xml import XMLEditor
from utils.errors import VmError, VmNotExistError, VmRunningError
from utils import errors
from .scheduler import HostMacIPScheduler, ScheduleError


def host_alive(host_ipv4:str, times=3, timeout=3):
    """
    检测目标主机是否可访问

    :param host_ipv4: 宿主机IP
    :param times: ping次数
    :param timeout:
    :return:
        True    # 可访问
        False   # 不可
    """
    cmd = f'ping -c {times} -i 0.1 -W {timeout} {host_ipv4}'
    res, info = subprocess.getstatusoutput(cmd)
    if res == 0:
        return True
    return False


class VmManager(VirtAPI):
    '''
    虚拟机元数据管理器
    '''
    VmError = VmError

    def get_vm_by_uuid(self, vm_uuid:str, related_fields:tuple=('mac_ip', 'host')):
        '''
        通过uuid获取虚拟机元数据

        :param vm_uuid: 虚拟机uuid hex字符串
        :param related_fields: 外键字段；外键字段直接一起获取，而不是惰性的用时再获取
        :return:
            Vm() or None     # success

        :raise:  VmError
        '''
        qs = self.get_vms_queryset()
        try:
            if related_fields:
                qs = qs.select_related(*related_fields).all()
            return qs.filter(uuid=vm_uuid).first()
        except Exception as e:
            raise VmError(msg=str(e))

    def get_vms_queryset(self):
        '''
        获取所有虚拟机的查询集
        :return: QuerySet()
        '''
        return Vm.objects.all()

    def get_user_vms_queryset(self, user):
        '''
        获取用户的虚拟机查询集
        :param user: 用户
        :return: QuerySet()
        '''
        return self.get_vms_queryset().filter(user=user).all()

    def _xml_edit_vcpu(self, xml_desc:str, vcpu:int):
        '''
        修改 xml中vcpu节点内容

        :param xml_desc: 定义虚拟机的xml内容
        :param vcpu: 虚拟cpu数
        :return:
            xml: str    # success

        :raise:  VmError
        '''
        xml = XMLEditor()
        if not xml.set_xml(xml_desc):
            raise VmError(msg='xml文本无效')

        root = xml.get_root()
        try:
            root.getElementsByTagName('vcpu')[0].firstChild.data = vcpu
        except Exception as e:
            raise VmError(msg='修改xml文本vcpu节点错误')
        return root.toxml()

    def _xml_edit_mem(self, xml_desc:str, mem:int):
        '''
        修改xml中mem节点内容

        :param xml_desc: 定义虚拟机的xml内容
        :param mem: 修改内存大小
        :return:
            xml: str    # success

        :raise:  VmError
        '''
        xml = XMLEditor()
        if not xml.set_xml(xml_desc):
            raise VmError(msg='xml文本无效')
        try:
            root = xml.get_root()
            node = root.getElementsByTagName('memory')[0]
            node.attributes['unit'].value = 'MiB'
            node.firstChild.data = mem

            node = root.getElementsByTagName('currentMemory')[0]
            node.attributes['unit'].value = 'MiB'
            node.firstChild.data = mem

            return root.toxml()
        except Exception as e:
            raise VmError(msg='修改xml文本memory节点错误')

    def get_vms_queryset_by_center(self, center_or_id):
        '''
        获取分中心下的虚拟机查询集

        :param center_or_id: 分中心对象或id
        :return:
            vms: QuerySet   # success
        :raise VmError
        '''
        try:
            group_ids = CenterManager().get_group_ids_by_center(center_or_id)
            host_ids = GroupManager().get_host_ids_by_group_ids(group_ids)
        except ComputeError as e:
            raise VmError(msg=str(e))

        return Vm.objects.filter(host__in=host_ids).all()

    def get_vms_queryset_by_group(self, group_or_id):
        '''
        获取宿主机组下的虚拟机查询集

        :param group_or_id: 宿主机组对象或id
        :return:
            vms: QuerySet   # success
        :raise VmError
        '''
        try:
            host_ids = GroupManager().get_all_host_ids_by_group(group_or_id)
        except ComputeError as e:
            raise VmError(msg=str(e))

        return Vm.objects.filter(host__in=host_ids).all()

    def get_vms_queryset_by_host(self, host_or_id):
        '''
        获取宿主机下的虚拟机查询集

        :param host_or_id: 宿主机对象或id
        :return:
            vms: QuerySet   # success
        :raise VmError
        '''
        return Vm.objects.filter(host=host_or_id).all()

    def filter_vms_queryset(self, center_id:int=0, group_id:int=0, host_id:int=0, user_id:int=0, search:str='',
                            all_no_filters:bool=False, related_fields:tuple=()):
        '''
        通过条件筛选虚拟机查询集

        :param center_id: 分中心id,大于0有效
        :param group_id: 宿主机组id,大于0有效
        :param host_id: 宿主机id,大于0有效
        :param user_id: 用户id,大于0有效
        :param search: 关键字筛选条件
        :param all_no_filters: 筛选条件都无效时；True: 返回所有； False: 抛出错误
        :param related_fields: 外键字段；外键字段直接一起获取，而不是惰性的用时再获取
        :return:
            QuerySet    # success

        :raise: VmError
        '''
        if not related_fields:
            related_fields = ('user', 'image', 'mac_ip__vlan', 'host')

        if center_id <= 0 and group_id <= 0 and host_id <= 0 and user_id <= 0 and not search:
            if not all_no_filters:
                raise VmError(msg='查询虚拟机条件无效')
            return self.get_vms_queryset().select_related(*related_fields).all()

        vm_queryset = None
        if host_id > 0:
            vm_queryset = self.get_vms_queryset_by_host(host_id)
        elif group_id > 0:
            vm_queryset = self.get_vms_queryset_by_group(group_id)
        elif center_id > 0:
            vm_queryset = self.get_vms_queryset_by_center(center_id)

        if user_id > 0:
            if vm_queryset is not None:
                vm_queryset = vm_queryset.filter(user=user_id).all()
            else:
                vm_queryset = self.get_user_vms_queryset(user_id)

        if search:
            if vm_queryset is not None:
                vm_queryset = vm_queryset.filter(Q(remarks__icontains=search) | Q(mac_ip__ipv4__icontains=search) |
                                                 Q(uuid__icontains=search)).all()
            else:
                vm_queryset = Vm.objects.filter(Q(remarks__icontains=search) | Q(mac_ip__ipv4__icontains=search) |
                                                 Q(uuid__icontains=search)).all()

        return vm_queryset.select_related(*related_fields).all()

    @staticmethod
    def get_vm_domain(host_ipv4: str, vm_uuid: str):
        """

        :param host_ipv4:
        :param vm_uuid:
        :return:
        """
        return VmDomain(host_ip=host_ipv4, vm_uuid=vm_uuid)

    def get_vm_xml_desc(self, host_ipv4:str, vm_uuid:str):
        '''
        动态从宿主机获取虚拟机的xml内容

        :param host_ipv4: 虚拟机所在的宿主机ip
        :param vm_uuid: 虚拟机uuid
        :return:
            xml: str    # success

        :raise VmError()
        '''
        domain = self.get_vm_domain(host_ipv4=host_ipv4, vm_uuid=vm_uuid)
        try:
            return domain.xml_desc()
        except self.VirtError as e:
            raise VmError(msg=str(e))

    def _xml_remove_sys_disk_auth(self, xml_desc:str):
        '''
        去除vm xml中系统盘节点ceph认证的auth

        :param xml_desc: 定义虚拟机的xml内容
        :return:
            xml: str    # success

        :raise:  VmError
        '''
        xml = XMLEditor()
        if not xml.set_xml(xml_desc):
            raise VmError(msg='虚拟机xml文本无效')

        root = xml.get_root()
        devices = root.getElementsByTagName('devices')
        if not devices:
            raise VmError(msg='虚拟机xml文本无效, 未找到devices节点')

        disks = devices[0].getElementsByTagName('disk')
        if not disks:
            raise VmError(msg='虚拟机xml文本无效, 未找到devices>disk节点')
        disk = disks[0]
        auth = disk.getElementsByTagName('auth')
        if not auth:
            return xml_desc

        disk.removeChild(auth[0])
        return root.toxml()

    def get_vm_vdisk_dev_list(self, vm:Vm):
        '''
        获取虚拟机所有硬盘的dev

        :param vm: 虚拟机对象
        :return:
            (disk:list, dev:list)    # disk = [disk_uuid, disk_uuid, ]; dev = ['vda', 'vdb', ]

        :raises: VmError
        '''
        xml_desc = self.get_vm_xml_desc(vm_uuid=vm.get_uuid(), host_ipv4=vm.host.ipv4)

        dev_list = []
        disk_list = []
        xml = XMLEditor()
        if not xml.set_xml(xml_desc):
            raise VmError(msg='虚拟机xml文本无效')

        root = xml.get_root()
        devices = root.getElementsByTagName('devices')[0].childNodes
        for d in devices:
            if d.nodeName == 'disk':
                for disk_child in d.childNodes:
                    if disk_child.nodeName == 'source':
                        pool_disk = disk_child.getAttribute('name')
                        disk = pool_disk.split('/')[-1]
                        disk_list.append(disk)
                    if disk_child.nodeName == 'target':
                        dev_list.append(disk_child.getAttribute('dev'))
        return disk_list, dev_list

    def new_vdisk_dev(self, dev_list:list):
        '''
        顺序从vda - vdz中获取下一个不包含在dev_list中的的dev字符串

        :param dev_list: 已使用的dev的list
        :return:
            str     # success
            None    # 没有可用的dev了
        '''
        # 从vdb开始，系统xml模板中系统盘驱动和硬盘一样为virtio时，硬盘使用vda会冲突错误
        for i in range(1, 26):
            dev = 'vd' + chr(ord('a') + i % 26)
            if dev not in dev_list:
                return dev

        return None

    def mount_disk(self, vm:Vm, disk_xml:str):
        '''
        向虚拟机挂载虚拟硬盘

        :param vm: 虚拟机对象
        :param disk_xml: 硬盘xml
        :return:
            True    # success
            False   # failed
        :raises: VmError
        '''
        host = vm.host
        domain = self.get_vm_domain(host_ipv4=host.ipv4, vm_uuid=vm.get_uuid())
        try:
            if domain.attach_device(xml=disk_xml):
                return True
            return False
        except self.VirtError as e:
            raise VmError(msg=f'挂载硬盘错误，{str(e)}')

    def umount_disk(self, vm:Vm, disk_xml:str):
        '''
        从虚拟机卸载虚拟硬盘

        :param vm: 虚拟机对象
        :param disk_xml: 硬盘xml
        :return:
            True    # success
            False   # failed
        :raises: VmError
        '''
        host = vm.host
        domain = self.get_vm_domain(host_ipv4=host.ipv4, vm_uuid=vm.get_uuid())
        try:
            if domain.detach_device(xml=disk_xml):
                return True
            return False
        except self.VirtError as e:
            raise VmError(msg=f'卸载硬盘错误，{str(e)}')

    def create_sys_disk_snap(self, vm:Vm, remarks:str):
        '''
        创建虚拟机系统盘快照
        :param vm: 虚拟机对象
        :param remarks: 备注信息
        :return:
            VmDiskSnap()    # success

        ::raises: VmError
        '''
        image = vm.image
        ceph_pool = image.ceph_pool
        disk_snap = VmDiskSnap(disk=vm.disk, vm=vm, ceph_pool=ceph_pool, remarks=remarks)
        try:
            disk_snap.save()
        except Exception as e:
            raise VmError(msg=str(e))

        return disk_snap

    def delete_sys_disk_snap(self, snap_id:int, user):
        '''
        删除虚拟机系统盘快照

        :param snap_id: 快照id
        :param user: 用户
        :return:
            True    # success

        :raises: VmError
        '''
        snap = VmDiskSnap.objects.select_related('vm', 'vm__user').filter(pk=snap_id).first()
        if not snap:
            raise VmError(msg='快照不存在')

        if not user.is_superuser:
            if snap.vm and not snap.vm.user_has_perms(user):
                raise VmError(msg='没有此快照的访问权限')

        try:
            snap.delete()
        except Exception as e:
            raise VmError(msg=str(e))

        return True

    def modify_sys_snap_remarks(self, snap_id:int, remarks:str, user):
        '''
        修改虚拟机系统盘快照备注信息

        :param snap_id: 快照id
        :param remarks: 备注信息
        :param user: 用户
        :return:
            VmDiskSnap()    # success
        :raises: VmError
        '''
        snap = VmDiskSnap.objects.select_related('vm', 'vm__user').filter(pk=snap_id).first()
        if not snap:
            raise VmError(msg='快照不存在')

        if not user.is_superuser:
            if snap.vm and not snap.vm.user_has_perms(user):
                raise VmError(msg='没有此快照的访问权限')

        try:
            snap.remarks = remarks
            snap.save(update_fields=['remarks'])
        except Exception as e:
            raise VmError(msg=str(e))

        return snap

    def disk_rollback_to_snap(self, vm:Vm, snap_id:int):
        '''
        回滚虚拟机系统盘到指定快照

        :param vm: 虚拟机对象
        :param snap_id: 快照id
        :param user: 用户
        :return:
            True    # success

        :raises: VmError
        '''
        snap = VmDiskSnap.objects.select_related('ceph_pool', 'ceph_pool__ceph').filter(pk=snap_id).first()
        if not snap:
            raise VmError(msg='快照不存在')

        if snap.disk != vm.disk:
            raise VmError(msg='快照不属于此主机')

        ceph_pool = snap.ceph_pool
        if not ceph_pool:
            raise VmError(msg='can not get ceph pool')
        pool_name = ceph_pool.pool_name
        config = ceph_pool.ceph
        if not config:
            raise VmError(msg='can not get ceph')

        try:
            rbd = get_rbd_manager(ceph=config, pool_name=pool_name)
            rbd.image_rollback_to_snap(image_name=vm.disk, snap=snap.snap)
        except (RadosError, Exception) as e:
            raise VmError(msg=str(e))

        return True

    def migrate_create_vm(self, vm, new_host):
        """
        虚拟机迁移目标宿主机上创建虚拟机

        :param vm: 虚拟机Vm()
        :param new_host: 目标宿主机Host()
        :return:
            Vm(), begin_create  # success
                begin_create: type bool; True：从新构建vm xml desc定义的vm，硬盘等设备需要重新挂载;
                            False：实时获取源vm xml desc, 原挂载的设备不受影响

        :raises: VmError
        """
        vm_uuid = vm.uuid
        xml_desc = None
        begin_create = False    # vm xml不是从新构建的

        # 实时获取vm xml desc
        try:
            xml_desc = self.get_vm_xml_desc(host_ipv4=vm.host.ipv4, vm_uuid=vm_uuid)
        except Exception as e:
            pass

        if not xml_desc:  # 实时获取vm xml, 从新构建虚拟机xml
            begin_create = True     # vm xml从新构建的
            try:
                xml_desc = self.build_vm_xml_desc(vm_uuid=vm_uuid, mem=vm.mem, vcpu=vm.vcpu, vm_disk_name=vm.disk,
                                                  image=vm.image, mac_ip=vm.mac_ip)
            except Exception as e:
                raise VmError(msg=f'构建虚拟机xml错误，{str(e)}')

        new_vm_define_ok = False
        try:
            # 创建虚拟机
            try:
                self.define(host_ipv4=new_host.ipv4, xml_desc=xml_desc)
            except VirtError as e:
                raise VmError(msg=str(e))
            new_vm_define_ok = True

            vm.host = new_host
            vm.xml = xml_desc
            try:
                vm.save(update_fields=['host', 'xml'])
            except Exception as e:
                raise VmError(msg='更新虚拟机元数据失败')

            return vm, begin_create
        except Exception as e:
            # 目标宿主机删除虚拟机
            if new_vm_define_ok:
                try:
                    self.undefine(host_ipv4=new_host.ipv4, vm_uuid=vm_uuid)
                except VirtError:
                    pass
            raise VmError(msg=str(e))

    def reset_image_create_vm(self, vm, new_image):
        """
        更换镜像创建虚拟机

        :param vm: 虚拟机Vm()
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
            new_pool_name = new_pool.pool_name
            new_data_pool = new_pool.data_pool if new_pool.has_data_pool else None
            new_ceph = new_pool.ceph

            old_vm_xml_desc = self.get_vm_xml_desc(vm_uuid=vm_uuid, host_ipv4=vm.host.ipv4)

            # 虚拟机xml
            xml_desc = self.build_vm_xml_desc(vm_uuid=vm_uuid, mem=vm.mem, vcpu=vm.vcpu, vm_disk_name=disk_name,
                                              image=new_image, mac_ip=vm.mac_ip)
            rbd_manager = get_rbd_manager(ceph=new_ceph, pool_name=new_pool_name)
        except Exception as e:
            raise VmError(msg=str(e))

        new_vm_define_ok = False
        new_disk_ok = False
        try:
            try:
                rbd_manager.clone_image(snap_image_name=new_image.base_image, snap_name=new_image.snap,
                                        new_image_name=disk_name, data_pool=new_data_pool)
            except ImageExistsError as e:
                pass
            new_disk_ok = True

            try:
                self.define(host_ipv4=host.ipv4, xml_desc=xml_desc)  # 新xml覆盖定义虚拟机
            except VirtError as e:
                raise VmError(msg=str(e))
            new_vm_define_ok = True

            vm.image = new_image
            vm.xml = xml_desc
            try:
                vm.save(update_fields=['image', 'xml'])
            except Exception as e:
                raise VmError(msg='更新虚拟机元数据失败')
            return vm
        except Exception as e:
            if new_disk_ok:
                try:
                    rbd_manager.remove_image(image_name=disk_name)  # 删除新的系统盘image
                except RadosError:
                    pass
            if new_vm_define_ok:
                try:
                    self.define(host_ipv4=host.ipv4, xml_desc=old_vm_xml_desc)  # 覆盖定义回原虚拟机
                except VirtError:
                    pass

            raise VmError(msg=str(e))

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
        vm = self.get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=())
        if vm is None:
            raise VmNotExistError(msg='虚拟机不存在')
        if not vm.user_has_perms(user=user):
            raise VmError(msg='当前用户没有权限访问此虚拟机')

        vm.remarks = remark
        try:
            vm.save(update_fields=['remarks'])
        except Exception as e:
            raise VmError(msg='更新备注信息失败')

        return True

    def get_vm_status(self, vm_uuid: str, user):
        """
        获取虚拟机的运行状态

        :param vm_uuid: 虚拟机uuid
        :param user: 用户
        :return:
            (state_code:int, state_str:str)     # success

        :raise VmError()
        """
        vm = self.get_vm_by_uuid(vm_uuid=vm_uuid)
        if vm is None:
            raise VmNotExistError(msg='虚拟机不存在')
        if not vm.user_has_perms(user=user):
            raise VmError(msg='当前用户没有权限访问此虚拟机')

        host = vm.host
        host_ip = host.ipv4
        try:
            domain = self.get_vm_domain(host_ipv4=host_ip, vm_uuid=vm_uuid)
            return domain.status()
        except VirtError as e:
            raise VmError(msg='获取虚拟机状态失败')

    def build_vm_xml_desc(self, vm_uuid: str, mem: int, vcpu: int, vm_disk_name: str, image, mac_ip):
        """
        构建虚拟机的xml
        :param vm_uuid:
        :param mem:
        :param vcpu:
        :param vm_disk_name: vm的系统盘镜像rbd名称
        :param image: 系统镜像实例
        :param mac_ip: MacIP实例
        :return:
            xml: str
        """
        pool = image.ceph_pool
        pool_name = pool.pool_name
        ceph = pool.ceph
        xml_tpl = image.xml_tpl.xml  # 创建虚拟机的xml模板字符串
        xml_desc = xml_tpl.format(name=vm_uuid, uuid=vm_uuid, mem=mem, vcpu=vcpu, ceph_uuid=ceph.uuid,
                                  ceph_pool=pool_name, diskname=vm_disk_name, ceph_username=ceph.username,
                                  ceph_hosts_xml=ceph.hosts_xml, mac=mac_ip.mac, bridge=mac_ip.vlan.br)

        if not ceph.has_auth:
            xml_desc = self._xml_remove_sys_disk_auth(xml_desc)

        return xml_desc


class VmArchiveManager:
    '''
    虚拟机归档管理类
    '''
    VmError = VmError

    def add_vm_archive(self, vm:Vm):
        '''
        添加一个虚拟机的归档记录

        :param vm: 虚拟机元数据对象
        :return:
            VmArchive() # success

        :raises:  VmError
        '''
        try:
            host = vm.host
            group = host.group
            center = group.center
            mac_ip = vm.mac_ip
            vlan = mac_ip.vlan
            image = vm.image
            ceph_pool = image.ceph_pool

            va = VmArchive(uuid=vm.get_uuid(), name=vm.name, vcpu=vm.vcpu, mem=vm.mem, disk=vm.disk, xml=vm.xml,
                           mac=mac_ip.mac, ipv4=mac_ip.ipv4, vlan_id=vlan.id, br=vlan.br,
                           image_id=image.id, image_parent=image.base_image, ceph_id=ceph_pool.ceph.id, ceph_pool=ceph_pool.pool_name,
                           center_id=center.id, center_name=center.name, group_id=group.id, group_name=group.name,
                           host_id=host.id, host_ipv4=host.ipv4, user=vm.user, create_time=vm.create_time, remarks=vm.remarks)
            va.save()
        except Exception as e:
            raise VmError(msg=str(e))
        return va

    @staticmethod
    def get_vm_archive(vm: Vm):
        return VmArchive.objects.filter(uuid=vm.get_uuid()).first()


class VmLogManager:
    '''
    虚拟机错误日志记录管理
    '''
    def __init__(self):
        self.vm_log = VmLog()

    @property
    def about(self):
        return self.vm_log

    def add_log(self, title:str, about:int, text:str):
        '''
        添加记录

        :param title: 记录标题
        :param about: 记录相关内容
        :param text: 记录内容
        :return:
            VmLog()     # success
            None        # failed
        '''
        about = VmLog.to_valid_about_value(about)
        try:
            log = VmLog(title=title, about=about, content=text)
            log.save()
        except Exception as e:
            return None

        return log


class FlavorManager:

    VmError = VmError

    def get_flavor_by_id(self, f_id: int):
        """
        通过uuid获取虚拟机元数据

        :param f_id:
        :return:
            Flavor() or None     # success

        :raise:  VmError
        """
        qs = self.get_flaver_queryset()
        try:
            return qs.filter(id=f_id).first()
        except Exception as e:
            raise VmError(msg=str(e))

    def get_flaver_queryset(self):
        """
        激活的样式
        :return: QuerySet()
        """
        return Flavor.objects.filter(enable=True).all()

    def get_public_flaver_queryset(self):
        """
        公开激活的样式

        :return: QuerySet()
        """
        return Flavor.objects.filter(enable=True, public=True).all()

    def get_user_flaver_queryset(self, user):
        """
        用户对应权限激活的样式

        :return: QuerySet()
        """
        if user.is_superuser:
            return self.get_flaver_queryset()
        return self.get_public_flaver_queryset()


class VmAPI:
    '''
    虚拟机API
    '''
    VmError = VmError

    def __init__(self):
        self._center_manager = CenterManager()
        self._group_manager = GroupManager()
        self._host_manager = HostManager()
        self._vm_manager = VmManager()
        self._image_manager = ImageManager()
        self._vlan_manager = VlanManager()
        self._macip_manager = MacIPManager()
        self._vdisk_manager = VdiskManager()
        self._pci_manager = PCIDeviceManager()

    def new_uuid_obj(self):
        '''
        生成一个新的uuid字符串
        :return: uuid:str
        '''
        return uuid.uuid4()

    def get_rbd_manager(self, ceph:CephCluster, pool_name:str):
        '''
        获取一个rbd管理接口对象

        :param ceph: ceph配置模型对象CephCluster()
        :param pool_name: pool名称
        :return:
            RbdManager()    # success
            raise VmError   # failed

        :raise VmError
        '''
        try:
            return get_rbd_manager(ceph=ceph, pool_name=pool_name)
        except RadosError as e:
            raise VmError(msg=str(e))

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

    def _get_user_shutdown_vm(self, vm_uuid: str, user, related_fields: tuple = ()):
        """
        获取用户有访问权的 关闭状态的 虚拟机

        :param vm_uuid: 虚拟机uuid
        :param user: 用户
        :param related_fields: 外键字段；外键字段直接一起获取，而不是惰性的用时再获取
        :return:
            Vm()   # success

        :raises: VmError
        """
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=related_fields)

        # 虚拟机的状态
        host = vm.host
        try:
            run = self._vm_manager.get_vm_domain(host_ipv4=host.ipv4, vm_uuid=vm_uuid).is_running()
        except VirtError as e:
            raise VmError(msg=f'获取虚拟机运行状态失败,{str(e)}')
        if run:
            raise VmRunningError(msg='虚拟机正在运行，请先关闭虚拟机')

        return vm

    def _get_image(self, image_id: int):
        '''
        获取image

        :return:
            Image()
            raise VmError

        :raise VmError
        '''
        try:
            image = self._image_manager.get_image_by_id(image_id, related_fields=('ceph_pool__ceph', 'xml_tpl'))
        except ImageError as e:
            raise VmError(err=e)
        if not image:
            raise VmError(msg='镜像ID参数有误，未找到指定系统镜像')
        if not image.enable:
            raise VmError(msg='镜像ID参数有误，镜像未启用')

        return image

    def _get_vlan(self, vlan_id:int):
        '''
           获取子网vlan

           :return:
               Vlan()
               raise VmError

           :raise VmError
           '''
        try:
            vlan = self._vlan_manager.get_vlan_by_id(vlan_id)
        except NetworkError as e:
            raise VmError(err=e)

        if not vlan:
            raise VmError(msg='子网ID有误，子网不存在')

        return vlan

    def _available_macip(self, ipv4: str, ip_public=None):
        """
       指定mac ip是否空闲可用，是否满足网络类型

       :return:
           MacIP()          # 可用
           raise VmError    # 不可用

       :raise VmError
       """
        try:
            mac_ip = self._macip_manager.get_macip_by_ipv4(ipv4=ipv4)
        except NetworkError as e:
            raise VmError(err=e)

        if not mac_ip:
            raise VmError(msg='mac ip不存在')

        if not mac_ip.can_used():
            raise VmError(msg='mac ip已被分配使用')

        if ip_public is None:       # 不指定ip类型
            return mac_ip

        vlan = mac_ip.vlan
        if not vlan:
            raise VmError(msg='mac ip未关联子网vlan，无法判断ip是公网或私网')

        if ip_public:  # 指定分配公网ip
            if not vlan.is_public():
                raise VmError(msg='指定的IP地址不是公网ip')
        else:  # 指定分配私网ip
            if vlan.is_public():
                raise VmError(msg='指定的IP地址不是私网ip')

        return mac_ip

    def _get_groups_host_check_perms(self, center_id: int, group_id: int, host_id: int, user):
        '''
        检查用户使用有宿主机组或宿主机访问权限，优先使用host_id

        :param group_id: 宿主机组ID
        :param host_id: 宿主机ID
        :param user: 用户
        :return:
                [], Host()          # host_id有效时
                [Group()], None     # host_id无效，group_id有效时

        :raises: VmError
        '''
        if host_id:
            try:
                host = self._host_manager.get_host_by_id(host_id)
            except ComputeError as e:
                raise VmError(msg=str(e))

            if not host:
                raise VmError(msg='指定宿主机不存在')
            # 用户访问宿主机权限检查
            if not host.user_has_perms(user=user):
                raise VmError(msg='当前用户没有指定宿主机的访问权限')

            return [], host

        if group_id:
            try:
                group = self._group_manager.get_group_by_id(group_id=group_id)
            except ComputeError as e:
                raise VmError(msg=f'查询宿主机组，{str(e)}')
            if not group:
                raise VmError(msg='指定宿主机组不存在')

            # 用户访问宿主机组权限检查
            if not group.user_has_perms(user=user):
                raise VmError(msg='当前用户没有指定宿主机的访问权限')

            return [group], None

        if center_id:
            try:
                groups = self._center_manager.get_user_group_queryset_by_center(center_or_id=center_id, user=user)
                groups = list(groups)
            except Exception as e:
                raise VmError(msg=f'查询指定分中心下的宿主机组错误，{str(e)}')

            return groups, None

        raise VmError(msg='必须指定一个有效的center id或者group id或者host id')

    def create_vm(self, image_id: int, vcpu: int, mem: int, vlan_id: int, user, center_id=None, group_id=None,
                  host_id=None, ipv4=None, remarks=None, ip_public=None, **kwargs):
        '''
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
        :return:
            Vm()
            raise VmError

        :raise VmError
        '''
        macip = None    # 申请的macip
        vlan = None
        diskname = None     # clone的系统镜像

        if vcpu <= 0:
            raise VmError(msg='无法创建虚拟机,vcpu参数无效')
        if mem <= 0:
            raise VmError(msg='无法创建虚拟机,men参数无效')
        if not ((center_id and center_id > 0) or (group_id and group_id > 0) or (host_id and host_id > 0)):
            raise VmError(msg='无法创建虚拟机,必须指定一个有效center_id或group_id或host_id参数')

        # 权限检查
        groups, host_or_none = self._get_groups_host_check_perms(center_id=center_id, group_id=group_id, host_id=host_id, user=user)
        image = self._get_image(image_id)    # 镜像

        vm_uuid_obj = self.new_uuid_obj()
        vm_uuid = vm_uuid_obj.hex

        ceph_pool = image.ceph_pool
        pool_name = ceph_pool.pool_name
        data_pool = ceph_pool.data_pool if ceph_pool.has_data_pool else None
        ceph_config = ceph_pool.ceph
        rbd_manager = self.get_rbd_manager(ceph=ceph_config, pool_name=pool_name)

        # 如果指定了vlan或ip
        if ipv4:
            self._available_macip(ipv4=ipv4, ip_public=ip_public)       # ip是否可用
            macip = self._macip_manager.apply_for_free_ip(ipv4=ipv4)    # 分配ip
            if not macip:
                raise VmError(msg='指定的IP地址不可用，不存在或已被占用')
        elif vlan_id and vlan_id > 0:
            vlan = self._get_vlan(vlan_id)  # 局域子网

        host = None     # 指示是否分配了宿主机和资源，指示创建失败时释放资源
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
            except ScheduleError as e:
                raise VmError(msg=f'申请资源错误,{str(e)}')
            if not macip:
                raise VmError(msg='申请mac ip失败')
            if not vlan:
                vlan = macip.vlan

            # 创建虚拟机的系统镜像disk
            try:
                rbd_manager.clone_image(snap_image_name=image.base_image, snap_name=image.snap, new_image_name=vm_uuid, data_pool=data_pool)
                diskname = vm_uuid
            except RadosError as e:
                raise VmError(msg=f'clone image error, {str(e)}')

            # 创建虚拟机
            vm = self._create_vm2(vm_uuid=vm_uuid, diskname=diskname, vcpu=vcpu, mem=mem, image=image,
                             vlan=vlan, host=host, macip=macip, user=user, remarks=remarks)
        except Exception as e:
            if macip:
                self._macip_manager.free_used_ip(ip_id=macip.id)  # 释放已申请的mac ip资源
            if host:
                self._host_manager.free_to_host(host_id=host.id, vcpu=vcpu, mem=mem) # 释放已申请的宿主机资源
            if diskname:
                try:
                    rbd_manager.remove_image(image_name=diskname)
                except RadosError:
                    pass

            raise VmError(msg=str(e))

        host.vm_created_num_add_1()  # 宿主机已创建虚拟机数量+1
        return vm

    def _create_vm2(self, vm_uuid:str, diskname:str, vcpu:int, mem:int, image, vlan, host, macip, user, remarks:str=''):
        '''
        仅创建虚拟机，不会清理传入的各种资源

        :param vm_uuid: 虚拟机uuid
        :param diskname: 系统盘uuid
        :param vcpu: cpu数
        :param mem: 内存大小
        :param vlan: 子网对象
        :param host: 宿主机对象
        :param macip: mac ip对象
        :param user: 用户对象
        :param remarks: 虚拟机备注信息
        :return:
            Vm()
            raise VmError

        :raises: VmError
        '''
        # 虚拟机xml
        try:
            xml_desc = self._vm_manager.build_vm_xml_desc(vm_uuid=vm_uuid, mem=mem, vcpu=vcpu, vm_disk_name=diskname,
                                                          image=image, mac_ip=macip)
        except Exception as e:
            raise VmError(msg=f'构建虚拟机xml错误,{str(e)}')

        try:
            # 创建虚拟机元数据
            vm = Vm(uuid=vm_uuid, name=vm_uuid, vcpu=vcpu, mem=mem, disk=diskname, user=user,
                    remarks=remarks, host=host, mac_ip=macip, xml=xml_desc, image=image)
            vm.save()
        except Exception as e:
            raise VmError(msg=f'创建虚拟机元数据错误,{str(e)}')

        # 创建虚拟机
        try:
            self._vm_manager.define(host_ipv4=host.ipv4, xml_desc=xml_desc)
        except VirtError as e:
            vm.delete()     # 删除虚拟机元数据
            raise VmError(msg=str(e))

        return vm

    def delete_vm(self, vm_uuid:str, user=None, force=False):
        '''
        删除一个虚拟机

        :param vm_uuid: 虚拟机uuid
        :param user: 用户
        :param force:   是否强制删除， 会强制关闭正在运行的虚拟机
        :return:
            True
            raise VmError

        :raise VmError
        '''
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=('host', 'user'))
        host = vm.host
        # 虚拟机的状态
        domain = self._vm_manager.get_vm_domain(host_ipv4=host.ipv4, vm_uuid=vm_uuid)
        if not force:   # 非强制删除
            try:
                run = domain.is_running()
            except VirDomainNotExist as e:
                run = False
            except VirtError as e:
                raise VmError(msg=f'获取虚拟机运行状态失败, {str(e)}')
            if run:
                raise VmRunningError(msg='虚拟机正在运行，请先关闭虚拟机')

        # 删除系统盘快照
        try:
            snaps = vm.sys_disk_snaps.all()
            for snap in snaps:
                snap.delete()
        except Exception as e:
            raise VmError(msg=f'删除虚拟机系统盘快照失败,{str(e)}')

        # 归档虚拟机
        try:
            vm_ahv = VmArchiveManager().add_vm_archive(vm)
        except VmError as e:
            vm_ahv = VmArchiveManager().get_vm_archive(vm)
            if not vm_ahv:
                raise VmError(msg=f'归档虚拟机失败，{str(e)}')

        log_manager = VmLogManager()

        # 删除虚拟机
        undefine_result = '已删除'
        try:
            if not domain.undefine():
                raise VmError(msg='删除虚拟机失败')
        except VirHostDown:
            vm_ahv.set_host_not_release()
            undefine_result = '未删除'
        except (VirtError, VmError):
            vm_ahv.delete()  # 删除归档记录
            raise VmError(msg='删除虚拟机失败')

        # 删除虚拟机元数据
        try:
            vm.delete()
        except Exception as e:
            msg = f'虚拟机（uuid={vm.get_uuid()}）{undefine_result}，并归档，但是虚拟机元数据删除失败;请手动删除虚拟机元数据。'
            log_manager.add_log(title='删除虚拟机元数据失败', about=log_manager.about.ABOUT_VM_METADATA, text=msg)
            raise VmError(msg='删除虚拟机元数据失败')

        # 宿主机已创建虚拟机数量-1
        if not host.vm_created_num_sub_1():
            msg = f'虚拟机（uuid={vm.get_uuid()}）{undefine_result}，并归档，宿主机（id={host.id}; ipv4={host.ipv4}）已创建虚拟机数量-1失败, 请手动-1。'
            log_manager.add_log(title='宿主机已创建虚拟机数量-1失败', about=log_manager.about.ABOUT_HOST_VM_CREATED, text=msg)

        # 释放mac ip
        mac_ip = vm.mac_ip
        if not mac_ip.set_free():
            msg = f'释放mac ip资源失败, 虚拟机uuid={vm.get_uuid()};\n mac_ip信息：{mac_ip.get_detail_str()};\n ' \
                  f'请查看核对虚拟机是否已成功删除并归档，如果已删除请手动释放此mac_ip资源'
            log_manager.add_log(title='释放mac ip资源失败', about=log_manager.about.ABOUT_MAC_IP, text=msg)

        # 卸载所有挂载的虚拟硬盘
        try:
            self._vdisk_manager.umount_all_from_vm(vm_uuid=vm_uuid)
        except VdiskError as e:
            msg = f'删除虚拟机时，卸载所有虚拟硬盘失败, 虚拟机uuid={vm.get_uuid()};\n' \
                  f'请查看核对虚拟机是否已删除归档，请手动解除所有虚拟硬盘与虚拟机挂载关系'
            log_manager.add_log(title='删除虚拟机时，卸载所有虚拟硬盘失败', about=log_manager.about.ABOUT_VM_DISK, text=msg)

        # 释放宿主机资源
        if not host.free(vcpu=vm.vcpu, mem=vm.mem):
            msg = f'释放宿主机资源失败, 虚拟机uuid={vm.get_uuid()};\n 宿主机信息：id={host.id}; ipv4={host.ipv4};\n' \
                  f'未释放资源：mem={vm.mem}MB;vcpu={vm.vcpu}；\n请查看核对虚拟机是否已成功删除并归档，如果已删除请手动释放此宿主机资源'
            log_manager.add_log(title='释放宿主机men, cpu资源失败', about=log_manager.about.ABOUT_MEM_CPU, text=msg)

        # vm系统盘RBD镜像修改了已删除归档的名称
        vm_ahv.rename_sys_disk_archive()
        return True

    def edit_vm_vcpu_mem(self, vm_uuid:str, vcpu:int=0, mem:int=0, user=None, force=False):
        '''
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
        '''
        if vcpu < 0 or mem < 0:
            raise VmError(msg='vcpu或mem不能小于0')

        if vcpu == 0 and mem == 0:
            return True

        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=('host', 'user'))
        # 没有变化直接返回
        if vm.vcpu == vcpu and vm.mem == mem:
            return True

        host = vm.host
        # 虚拟机的状态
        domain = self._vm_manager.get_vm_domain(host_ipv4=host.ipv4, vm_uuid=vm_uuid)
        try:
            run = domain.is_running()
        except VirtError as e:
            raise VmError(msg='获取虚拟机运行状态失败')
        if run:
            if not force:
                raise VmRunningError(msg='虚拟机正在运行，请先关闭虚拟机')
            try:
                domain.poweroff()
            except VirtError as e:
                raise VmError(msg='强制关闭虚拟机失败')

        xml_desc = domain.xml_desc()
        try:
            # 修改vcpu
            if vcpu > 0 and vcpu != vm.vcpu:
                # vcpu增大
                if vcpu > vm.vcpu:
                    vcpu_need = vcpu - vm.vcpu
                    # 宿主机是否满足资源需求
                    if not host.meet_needs(vcpu=vcpu_need, mem=0):
                        raise VmError(msg='宿主机已没有足够的vcpu资源')

                    if not host.claim(vcpu=vcpu_need, mem=0):
                        raise VmError(msg='向宿主机申请的vcpu资源失败')
                else:
                    vcpu_free = vm.vcpu - vcpu
                    if not host.free(vcpu=vcpu_free, mem=0):
                        raise VmError(msg='释放宿主机vcpu资源失败')

                try:
                    xml_desc = self._vm_manager._xml_edit_vcpu(xml_desc=xml_desc, vcpu=vcpu)
                except VmError as e:
                    raise e

                vm.vcpu = vcpu

            if mem > 0 and mem != vm.mem:
                # vcpu增大
                if mem > vm.mem:
                    mem_need = mem - vm.mem
                    # 宿主机是否满足资源需求
                    if not host.meet_needs(vcpu=0, mem=mem_need):
                        raise VmError(msg='宿主机已没有足够的内存资源')

                    if not host.claim(vcpu=0, mem=mem_need):
                        raise VmError(msg='向宿主机申请的内存资源失败')
                else:
                    mem_free = vm.mem - mem
                    if not host.free(vcpu=0, mem=mem_free):
                        raise VmError(msg='释放宿主机内存资源失败')

                try:
                    xml_desc = self._vm_manager._xml_edit_mem(xml_desc=xml_desc, mem=mem)
                except VmError as e:
                    raise e

                vm.mem = mem

            # 创建虚拟机
            try:
                if not self._vm_manager.define(host_ipv4=host.ipv4, xml_desc=xml_desc):
                    raise VmError(msg='修改虚拟机失败')
            except VirtError as e:
                raise VmError(msg='修改虚拟机失败')

            vm.xml = xml_desc
        except VmError as e:
                raise e

        try:
            vm.save()
        except Exception as e:
            raise VmError(msg=f'修改虚拟机元数据失败, {str(e)}')

        return True

    def vm_operations(self, vm_uuid:str, op:str, user):
        '''
        操作虚拟机

        :param vm_uuid: 虚拟机uuid
        :param op: 操作，['start', 'reboot', 'shutdown', 'poweroff', 'delete', 'delete_force']
        :param user: 用户
        :return:
            True    # success
            False   # failed
        :raise VmError
        '''
        # 删除操作
        try:
            if op == 'delete':
                return self.delete_vm(vm_uuid=vm_uuid, user=user)
            elif op == 'delete_force':
                return self.delete_vm(vm_uuid=vm_uuid, force=True, user=user)
        except VmError as e:
            raise e

        # 普通操作
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=('host', 'user'))
        host_ip = vm.host.ipv4

        try:
            domain = self._vm_manager.get_vm_domain(host_ipv4=host_ip, vm_uuid=vm_uuid)
            if op == 'start':
                return domain.start()
            elif op == 'reboot':
                return domain.reboot()
            elif op == 'shutdown':
                return domain.shutdown()
            elif op == 'poweroff':
                return domain.poweroff()
            else:
                raise VmError(msg='无效的操作')
        except VirtError as e:
            raise VmError(msg=str(e))

    def get_vm_status(self, vm_uuid:str, user):
        '''
        获取虚拟机的运行状态

        :param vm_uuid: 虚拟机uuid
        :param user: 用户
        :return:
            (state_code:int, state_str:str)     # success

        :raise VmError()
        '''
        return self._vm_manager.get_vm_status(vm_uuid=vm_uuid, user=user)

    def modify_vm_remark(self, vm_uuid:str, remark:str, user):
        '''
        修改虚拟机备注信息

        :param vm_uuid: 虚拟机uuid
        :param remark: 新的备注信息
        :param user: 用户
        :return:
            True       # success
        :raise VmError()
        '''
        return self._vm_manager.modify_vm_remark(vm_uuid=vm_uuid, remark=remark, user=user)

    def mount_disk(self, vm_uuid:str, vdisk_uuid:str, user):
        '''
        向虚拟机挂载硬盘

        :param vm_uuid: 虚拟机uuid
        :param vdisk_uuid: 虚拟硬盘uuid
        :param user: 用户
        :return:
            Vdisk()    # success

        :raises: VmError
        '''
        try:
            vdisk = self._vdisk_manager.get_vdisk_by_uuid(uuid=vdisk_uuid, related_fields=('quota', 'quota__group'))
        except VdiskError as e:
            raise VmError(msg='查询硬盘时错误')

        if vdisk is None:
            raise VmError(msg='硬盘不存在')
        if not vdisk.enable:
            raise VmError(msg='硬盘暂不可使用')
        if not vdisk.user_has_perms(user=user):
            raise VmError(msg='当前用户没有权限访问此硬盘')

        vm = self._get_user_shutdown_vm(vm_uuid=vm_uuid, user=user, related_fields=('host__group', 'user'))
        host = vm.host
        if host.group != vdisk.quota.group:
            raise VmError(msg='虚拟机和硬盘不再同一个机组')

        disk_list, dev_list = self._vm_manager.get_vm_vdisk_dev_list(vm=vm)
        if vdisk_uuid in disk_list:
            return vdisk

        dev = self._vm_manager.new_vdisk_dev(dev_list)
        if not dev:
            raise VmError(msg='不能挂载更多的硬盘了')

        # 硬盘元数据和虚拟机建立挂载关系
        try:
            self._vdisk_manager.mount_to_vm(vdisk_uuid=vdisk_uuid, vm=vm, dev=dev)
        except VdiskError as e:
            raise VmError(msg=str(e))

        # 向虚拟机挂载硬盘
        try:
            xml = vdisk.xml_desc(dev=dev)
            self._vm_manager.mount_disk(vm=vm, disk_xml=xml)
        except (VmError, Exception) as e:
            try:
                self._vdisk_manager.umount_from_vm(vdisk_uuid=vdisk_uuid)
            except VdiskError:
                msg = f'硬盘与虚拟机解除挂载关系失败, 虚拟机uuid={vm.get_uuid()};\n' \
                      f'硬盘uuid={vdisk.uuid};\n 请查看核对此硬盘是否被挂载到此虚拟机，如果已挂载到此虚拟机，' \
                      f'请忽略此记录，如果未挂载，请手动解除与虚拟机挂载关系'
                log_manager = VmLogManager()
                log_manager.add_log(title='硬盘与虚拟机解除挂载关系失败', about=log_manager.about.ABOUT_VM_DISK, text=msg)
            raise VmError(msg=str(e))

        # 更新vm元数据中的xml
        try:
            xml_desc = self._vm_manager.get_vm_xml_desc(vm_uuid=vm.get_uuid(), host_ipv4=vm.host.ipv4)
            vm.xml = xml_desc
            vm.save(update_fields=['xml'])
        except Exception:
            pass

        return vdisk

    def umount_disk(self, vdisk_uuid:str, user):
        '''
        从虚拟机卸载硬盘

        :param vdisk_uuid: 虚拟硬盘uuid
        :param user: 用户
        :return:
            Vdisk()    # success

        :raises: VmError
        '''
        try:
            vdisk = self._vdisk_manager.get_vdisk_by_uuid(uuid=vdisk_uuid, related_fields=('vm', 'vm__host'))
        except VdiskError as e:
            raise VmError(msg='查询硬盘时错误')

        if vdisk is None:
            raise VmError(msg='硬盘不存在')

        if not vdisk.user_has_perms(user=user):
            raise VmError(msg='当前用户没有权限访问此硬盘')

        vm = vdisk.vm
        if not vm:
            return vdisk

        if not vm.user_has_perms(user=user):
            raise VmError(msg='当前用户没有权限访问此虚拟机')

        # 虚拟机的状态
        host = vm.host
        domain = self._vm_manager.get_vm_domain(host_ipv4=host.ipv4, vm_uuid=vm.hex_uuid)
        try:
            run = domain.is_running()
        except VirtError as e:
            raise VmError(msg='获取虚拟机运行状态失败')
        if run:
            raise VmRunningError(msg='虚拟机正在运行，请先关闭虚拟机')

        # 从虚拟机卸载硬盘
        xml = vdisk.xml_desc()
        try:
            self._vm_manager.umount_disk(vm=vm, disk_xml=xml)
        except VmError as e:
            raise e

        # 硬盘元数据和虚拟机解除挂载关系
        try:
            self._vdisk_manager.umount_from_vm(vdisk_uuid=vdisk_uuid)
        except VdiskError as e:
            try:
                self._vm_manager.mount_disk(vm=vm, disk_xml=xml)
            except VmError:
                pass
            raise VmError(msg=str(e))

        # 更新vm元数据中的xml
        try:
            xml_desc = domain.xml_desc()
            vm.xml = xml_desc
            vm.save(update_fields=['xml'])
        except Exception:
            pass

        return vdisk

    def create_vm_sys_snap(self, vm_uuid:str, remarks:str, user):
        '''
        创建虚拟机系统盘快照
        :param vm_uuid: 虚拟机id
        :param remarks: 快照备注信息
        :param user: 用户
        :return:
            VmDiskSnap()    # success
        :raises: VmError
        '''
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=('user', 'image__ceph_pool__ceph'))

        # 虚拟机的状态
        # host = vm.host
        # try:
        #     run = self._vm_manager.is_running(host_ipv4=host.ipv4, vm_uuid=vm.hex_uuid)
        # except VirtError as e:
        #     raise VmError(msg='获取虚拟机运行状态失败')
        # if run:
        #     raise VmRunningError(msg='虚拟机正在运行，请先关闭虚拟机')

        snap = self._vm_manager.create_sys_disk_snap(vm=vm, remarks=remarks)
        return snap

    def vm_rollback_to_snap(self, vm_uuid:str, snap_id:int, user):
        '''
        回滚虚拟机系统盘到指定快照

        :param vm_uuid: 虚拟机id
        :param snap_id: 快照id
        :param user: 用户
        :return:
           True    # success

        :raises: VmError
        '''
        vm = self._get_user_shutdown_vm(vm_uuid=vm_uuid, user=user, related_fields=())
        return self._vm_manager.disk_rollback_to_snap(vm=vm, snap_id=snap_id)

    def umount_pci_device(self, device_id:int, user):
        '''
        从虚拟机卸载pci设备

        :param device_id: pci设备id
        :param user: 用户
        :return:
            PCIDevice()    # success

        :raises: VmError
        '''
        try:
            device = self._pci_manager.get_device_by_id(device_id=device_id, related_fields=('host',))
        except DeviceError as e:
            raise VmError(msg='查询设备时错误')

        if device is None:
            raise VmError(msg='设备不存在')
        if not device.enable:
            raise VmError(msg='设备暂不可使用')
        if not device.user_has_perms(user=user):
            raise VmError(msg='当前用户没有权限访问此设备')

        vm = device.vm
        if vm is None:
            return True
        if not vm.user_has_perms(user=user):
            raise VmError(msg='当前用户没有权限访问此虚拟机')

        # 虚拟机的状态
        host = vm.host
        domain = self._vm_manager.get_vm_domain(host_ipv4=host.ipv4, vm_uuid=vm.hex_uuid)
        try:
            run = domain.is_running()
        except VirtError as e:
            raise VmError(msg='获取虚拟机运行状态失败')
        if run:
            raise VmRunningError(msg='虚拟机正在运行，请先关闭虚拟机')

        # 卸载设备
        try:
            self._pci_manager.umount_from_vm(device=device)
        except DeviceError as e:
            raise VmError(msg=str(e))

        # 更新vm元数据中的xml
        try:
            xml_desc = domain.xml_desc()
            vm.xml = xml_desc
            vm.save(update_fields=['xml'])
        except Exception:
            pass

        return device

    def mount_pci_device(self, vm_uuid:str, device_id:int, user):
        '''
        向虚拟机挂载pci设备

        :param vm_uuid: 虚拟机uuid
        :param device_id: pci设备id
        :param user: 用户
        :return:
            PCIDevice()   # success

        :raises: VmError
        '''
        try:
            device = self._pci_manager.get_device_by_id(device_id=device_id, related_fields=('host',))
        except DeviceError as e:
            raise VmError(msg='查询设备时错误')

        if device is None:
            raise VmError(msg='设备不存在')
        if not device.enable:
            raise VmError(msg='设备暂不可使用')
        if not device.user_has_perms(user=user):
            raise VmError(msg='当前用户没有权限访问此设备')

        vm = self._get_user_shutdown_vm(vm_uuid=vm_uuid, user=user, related_fields=('user', 'host__group'))
        # 向虚拟机挂载
        try:
            self._pci_manager.mount_to_vm(vm=vm, device=device)
        except DeviceError as e:
            raise VmError(msg=str(e))

        # 更新vm元数据中的xml
        try:
            xml_desc = self._vm_manager.get_vm_xml_desc(vm_uuid=vm.get_uuid(), host_ipv4=vm.host.ipv4)
            vm.xml = xml_desc
            vm.save(update_fields=['xml'])
        except Exception:
            pass

        return device

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
        vm = self._get_user_shutdown_vm(vm_uuid=vm_uuid, user=user, related_fields=(
            'user', 'host__group', 'image__ceph_pool__ceph'))

        new_image = self._get_image(image_id)  # 镜像
        # 同一个iamge
        if new_image.pk == vm.image.pk:
            return self._reset_vm_sys_disk(vm)

        # vm和image是否在同一个分中心
        host = vm.host
        if host.group.center_id != new_image.ceph_pool.ceph.center_id:
            raise VmError(msg='虚拟机和系统镜像不在同一个分中心')

        # 删除快照记录
        try:
            vm.sys_snaps.delete()
        except Exception as e:
            raise VmError(msg=f'删除虚拟机系统盘快照失败，{str(e)}')

        # rename sys disk
        disk_name = vm.disk
        old_pool = vm.image.ceph_pool
        old_pool_name = old_pool.pool_name
        old_ceph = old_pool.ceph
        ok, deleted_disk = rename_sys_disk_delete(ceph=old_ceph, pool_name=old_pool_name, disk_name=disk_name)
        if not ok:
            raise VmError(msg='虚拟机系统盘重命名失败')

        try:
            vm = self._vm_manager.reset_image_create_vm(vm=vm, new_image=new_image)
        except VmError as e:
            # 原系统盘改回原名
            rename_image(ceph=old_ceph, pool_name=old_pool_name, image_name=deleted_disk, new_name=disk_name)
            raise VmError(msg=str(e))

        # 向虚拟机挂载硬盘
        for vdisk in vm.vdisks:
            vdisk_xml = vdisk.xml_desc(dev=vdisk.dev)
            try:
                self._vm_manager.mount_disk(vm=vm, disk_xml=vdisk_xml)
            except VmError as e:
                self._vdisk_manager.umount_from_vm(vdisk_uuid=vdisk.uuid)

        # PCI设备
        for dev in vm.pci_devices:
            try:
                self._pci_manager.mount_to_vm(vm=vm, device=dev)
            except DeviceError as e:
                raise VmError(msg=str(e))

        # 更新vm元数据中的xml
        try:
            xml_desc = self._vm_manager.get_vm_xml_desc(vm_uuid=vm.get_uuid(), host_ipv4=vm.host.ipv4)
            vm.xml = xml_desc
            vm.save(update_fields=['xml'])
        except Exception:
            pass

        return vm

    def migrate_vm(self, vm_uuid: str, host_id: int, user, force: bool = False):
        """
        迁移虚拟机

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

        # 虚拟机的状态
        is_host_down = False
        host = vm.host
        try:
            run = self._vm_manager.get_vm_domain(host_ipv4=host.ipv4, vm_uuid=vm_uuid).is_running()
        except VirHostDown as e:
            is_host_down = True
            if not force:
                raise VmError(msg=f'无法连接宿主机,{str(e)}')
        except VirDomainNotExist as e:
            pass
        except VirtError as e:
            raise VmError(msg=f'获取虚拟机运行状态失败,{str(e)}')
        else:
            if run:
                if not force:
                    raise VmRunningError(msg='虚拟机正在运行，请先关闭虚拟机')

                # 强制迁移，先尝试断电
                try:
                    self._vm_manager.get_vm_domain(host_ipv4=host.ipv4, vm_uuid=vm_uuid).poweroff()
                except VirtError as e:
                    pass

        # if force and is_host_down:
        #     alive = host_alive(vm.ipv4)
        #     if alive:
        #         raise VmError(msg='宿主机无法连接，但是探测到虚拟主机处于活动状态，未防止导致网络冲突，不允许强制迁移。')

        # 是否同宿主机组
        old_host = vm.host
        try:
            new_host = self._host_manager.get_host_by_id(host_id=host_id)
        except ComputeError as e:
            raise VmError(msg=str(e))
        if not new_host:
            raise VmError(msg='指定的目标宿主机不存在')

        if old_host.id == new_host.id:
            raise VmError(msg='不能在同一个宿主机上迁移')
        if new_host.group_id != old_host.group_id:
            raise VmError(msg='目标宿主机和云主机宿主机不在同一个机组')

        # 检测目标宿主机是否处于活动状态
        alive = host_alive(new_host.ipv4)
        if not alive:
            raise VmError(msg='目标宿主机处于未活动状态，请重新选择迁移目标宿主机')

        # PCI设备
        pci_devices = vm.pci_devices
        if pci_devices:
            if not force:
                raise VmError(msg='请先卸载主机挂载的PCI设备')

            # 卸载设备
            for device in pci_devices:
                try:
                    device.umount()
                except DeviceError as e:
                    raise DeviceError(msg=f'卸载主机挂载的PCI设备失败, {str(e)}')

        # 目标宿主机资源申请
        try:
            new_host = self._host_manager.claim_from_host(host_id=host_id, vcpu=vm.vcpu, mem=vm.mem)
        except ComputeError as e:
            raise VmError(msg=str(e))

        # 目标宿主机创建虚拟机
        try:
            vm, from_begin_create = self._vm_manager.migrate_create_vm(vm=vm, new_host=new_host)
        except Exception as e:
            # 释放目标宿主机资源
            new_host.free(vcpu=vm.vcpu, mem=vm.mem)
            raise VmError(msg=str(e))

        new_host.vm_created_num_add_1()  # 宿主机虚拟机数+1

        log_msg = ''
        if from_begin_create:   # 重新构建vm xml创建的vm, 需要重新挂载硬盘等设备
            # 向虚拟机挂载硬盘
            vdisks = vm.vdisks
            for vdisk in vdisks:
                try:
                    xml = vdisk.xml_desc(dev=vdisk.dev)
                    self._vm_manager.mount_disk(vm=vm, disk_xml=xml)
                except (VmError, Exception) as e:
                    log_msg += f'vdisk(uuid={vdisk.uuid}) 挂载失败,err={str(e)}；\n'
                    try:
                        self._vdisk_manager.umount_from_vm(vdisk_uuid=vdisk.uuid)
                    except VdiskError as e2:
                        log_msg += f'vdisk(uuid={vdisk.uuid})和vm(uuid={vm_uuid}元数据挂载关系解除失败),err={str(e2)}；\n'

            # 如果挂载了硬盘，更新vm元数据中的xml
            if vdisks:
                try:
                    xml_desc = self._vm_manager.get_vm_xml_desc(vm_uuid=vm.get_uuid(), host_ipv4=vm.host.ipv4)
                    vm.xml = xml_desc
                    vm.save(update_fields=['xml'])
                except Exception:
                    pass

        # 删除原宿主机上的虚拟机
        src_vm_undefined = False
        try:
            ok = self._vm_manager.undefine(host_ipv4=old_host.ipv4, vm_uuid=vm_uuid)
            if not ok:
                raise VirtError(msg='删除原宿主机上的虚拟机失败')
            src_vm_undefined = True
            old_host.vm_created_num_sub_1()  # 宿主机虚拟机数-1
        except VirtError as e:
            log_msg += f'源host({old_host.ipv4})上的vm(uuid={vm_uuid})删除失败，err={str(e)};\n'

        # 源宿主机资源释放
        if not old_host.free(vcpu=vm.vcpu, mem=vm.mem):
            log_msg += f'源host({old_host.ipv4})资源(vcpu={vm.vcpu}, mem={vm.mem}MB)释放失败;\n'

        # 迁移日志
        result = False
        if not log_msg:
            log_msg = '迁移正常'
            result = True
        try:
            m_log = MigrateLog(vm_uuid=vm_uuid, src_host_id=old_host.id, src_host_ipv4=old_host.ipv4,
                               dst_host_id=new_host.id, dst_host_ipv4=new_host.ipv4, result=result,
                               content=log_msg, src_undefined=src_vm_undefined)
            m_log.save()
        except Exception as e:
            pass

        return vm

    def _reset_vm_sys_disk(self, vm: Vm):
        """
        重置虚拟机系统盘，恢复到创建时状态

        :param vm: 虚拟机对象; type Vm
        :return:
            Vm()   # success

        :raises: VmError
        """
        # 删除快照记录
        try:
            vm.sys_snaps.delete()
        except Exception as e:
            raise VmError(msg=f'删除虚拟机系统盘快照失败，{str(e)}')

        disk_name = vm.disk
        pool = vm.image.ceph_pool
        pool_name = pool.pool_name
        ceph = pool.ceph
        image = vm.image
        data_pool = pool.data_pool if pool.has_data_pool else None

        ok, deleted_disk = rename_sys_disk_delete(ceph=ceph, pool_name=pool_name, disk_name=disk_name)
        if not ok:
            raise VmError(msg='虚拟机系统盘重命名失败')

        rbd_manager = get_rbd_manager(ceph=ceph, pool_name=pool_name)
        try:
            rbd_manager.clone_image(snap_image_name=image.base_image, snap_name=image.snap,
                                    new_image_name=disk_name, data_pool=data_pool)
        except (RadosError, ImageExistsError) as e:
            # 原系统盘改回原名
            rename_image(ceph=ceph, pool_name=pool_name, image_name=deleted_disk, new_name=disk_name)
            raise VmError(msg=f'虚拟机系统盘创建失败, {str(e)}')

        return vm

    def reset_sys_disk(self, vm_uuid: str, user):
        """
        重置虚拟机系统盘，恢复到创建时状态

        :param vm_uuid: 虚拟机uuid
        :param user: 用户
        :return:
            Vm()   # success

        :raises: VmError
        """
        vm = self._get_user_shutdown_vm(vm_uuid=vm_uuid, user=user, related_fields=(
            'user', 'host__group', 'image__ceph_pool__ceph'))

        return self._reset_vm_sys_disk(vm)

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
        image = vm.image
        if image.sys_type not in [image.SYS_TYPE_LINUX, image.SYS_TYPE_UNIX]:
            raise VmError(msg=f'只支持linux或unix系统虚拟主机修改密码')

        # 虚拟机的状态
        host = vm.host
        try:
            run = self._vm_manager.get_vm_domain(host_ipv4=host.ipv4, vm_uuid=vm_uuid).is_running()
        except VirtError as e:
            raise VmError(msg=f'获取虚拟机运行状态失败,{str(e)}')
        if not run:
            raise VmError(msg='虚拟机没有运行')

        domain = self._vm_manager.get_vm_domain(host_ipv4=host.ipv4, vm_uuid=vm_uuid)
        try:
            ok = domain.set_user_password(username=username, password=password)
        except VirtError as e:
            raise VmError(msg=f'修改密码失败，{str(e)}')

        if not ok:
            raise VmError(msg='修改密码失败')

        try:
            vm.init_password = password
            vm.save(update_fields=['init_password'])
        except Exception:
            pass
        return vm

    def vm_miss_fix(self, vm_uuid: str, user):
        """
        宿主机上虚拟机丢失修复

        :param vm_uuid: 虚拟机uuid
        :param user: 用户
        :return:
            Vm()   # success

        :raises: VmError
        """
        vm = self._get_user_perms_vm(vm_uuid=vm_uuid, user=user, related_fields=('host', 'user', 'image__ceph_pool__ceph'))
        host = vm.host
        # 虚拟机
        domain = self._vm_manager.get_vm_domain(host_ipv4=host.ipv4, vm_uuid=vm_uuid)
        try:
            ok = domain.exists()
        except VirHostDown as e:
            raise VmError(msg=f'无法连接宿主机', err_code='HostDown')
        except VirtError as e:
            raise VmError(msg=f'确认宿主机上是否丢失虚拟机时错误, {str(e)}')
        if ok:
            raise errors.VmAlreadyExistError(msg='虚拟主机未丢失, 无需修复')

        # disk rbd是否存在
        image = vm.image
        disk_name = vm.disk
        try:
            rbd_mgr = get_rbd_manager(ceph=image.ceph_pool.ceph, pool_name=image.ceph_pool.pool_name)
            ok = rbd_mgr.image_exists(image_name=disk_name)
        except RadosError as e:
            raise VmError(msg=f'查询虚拟主机系统盘镜像时错误，{str(e)}')

        if not ok:
            raise errors.VmDiskImageMissError(msg=f'虚拟主机系统盘镜像不存在，无法恢复此虚拟主机')

        try:
            xml_desc = self._vm_manager.build_vm_xml_desc(vm_uuid=vm_uuid, mem=vm.mem, vcpu=vm.vcpu, vm_disk_name=disk_name,
                                                          image=image, mac_ip=vm.mac_ip)
        except Exception as e:
            raise VmError(msg=f'构建虚拟主机xml错误，{str(e)}')

        # 创建虚拟机
        try:
            self._vm_manager.define(host_ipv4=host.ipv4, xml_desc=xml_desc)
        except VirtError as e:
            raise VmError(msg=f'宿主机上创建虚拟主机错误，{str(e)}')

        return vm

