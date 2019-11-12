import uuid
import os

from django.db.models import Q

from ceph.managers import RadosError, RbdManager
from ceph.models import CephCluster
from compute.managers import CenterManager, GroupManager, HostManager, ComputeError
from image.managers import ImageManager, ImageError
from network.managers import VlanManager, MacIPManager, NetworkError
from network.models import Vlan
from vdisk.manager import VdiskManager, VdiskError
from utils.ev_libvirt.virt import VirtAPI, VirtError
from .models import Vm, VmArchive, VmLog
from .xml import XMLEditor


class VmError(Exception):
    '''
    虚拟机相关错误定义
    '''
    def __init__(self, code:int=0, msg:str='', err=None):
        '''
        :param code: 错误码
        :param msg: 错误信息
        :param err: 错误对象
        '''
        self.code = code
        self.msg = msg
        self.err = err

    def __str__(self):
        return self.detail()

    def detail(self):
        '''错误详情'''
        if self.msg:
            return self.msg

        if self.err:
            return str(self.err)

        return '未知的错误'


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
                qs.select_related(*related_fields)
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
            host_ids = GroupManager().get_hsot_ids_by_group_ids(group_ids)
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
            host_ids = GroupManager().get_host_ids_by_group(group_or_id)
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

    def filter_vms_queryset(self, center_id:int=0, group_id:int=0, host_id:int=0, user_id:int=0, search:str='', all_no_filters:bool=False):
        '''
        通过条件筛选虚拟机查询集

        :param center_id: 分中心id,大于0有效
        :param group_id: 宿主机组id,大于0有效
        :param host_id: 宿主机id,大于0有效
        :param user_id: 用户id,大于0有效
        :param search: 关键字筛选条件
        :param all_no_filters: 筛选条件都无效时；True: 返回所有； False: 抛出错误
        :return:
            QuerySet    # success

        :raise: VmError
        '''
        if center_id <= 0 and group_id <= 0 and host_id <= 0 and user_id <= 0 and not search:
            if not all_no_filters:
                raise VmError(msg='查询虚拟机条件无效')
            return self.get_vms_queryset().select_related('user', 'image', 'mac_ip', 'host').all()

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
            if vm_queryset:
                vm_queryset = vm_queryset.filter(Q(remarks__icontains=search) | Q(mac_ip__ipv4__icontains=search) |
                                                 Q(uuid__icontains=search)).all()
            else:
                vm_queryset = Vm.objects.filter(Q(remarks__icontains=search) | Q(mac_ip__ipv4__icontains=search) |
                                                 Q(uuid__icontains=search)).all()

        return vm_queryset.select_related('user', 'image', 'mac_ip', 'host').all()

    def get_vm_xml_desc(self, host_ipv4:str, vm_uuid:str):
        '''
        动态从宿主机获取虚拟机的xml内容

        :param host_ipv4: 虚拟机所在的宿主机ip
        :param vm_uuid: 虚拟机uuid
        :return:
            xml: str    # success

        :raise VmError()
        '''
        try:
            xml_desc = self.get_domain_xml_desc(host_ipv4=host_ipv4, vm_uuid=vm_uuid)
            return  xml_desc
        except self.VirtError as e:
            raise VmError(msg=str(e))

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
        return (disk_list, dev_list)

    def new_vdisk_dev(self, dev_list:list):
        '''
        顺序从vda - vdz中获取下一个不包含在dev_list中的的dev字符串

        :param dev_list: 已使用的dev的list
        :return:
            str     # success
            None    # 没有可用的dev了
        '''
        for i in range(0, 26):
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
        try:
            if self.attach_device(host_ipv4=host.ipv4, vm_uuid=vm.get_uuid(), xml=disk_xml):
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
        try:
            if self.detach_device(host_ipv4=host.ipv4, vm_uuid=vm.get_uuid(), xml=disk_xml):
                return True
            return False
        except self.VirtError as e:
            raise VmError(msg=f'卸载硬盘错误，{str(e)}')


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


class VmLogManager():
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
        conf_file = ceph.config_file
        keyring_file = ceph.keyring_file
        # 当水平部署多个服务时，在后台添加ceph配置时，只有其中一个服务保存了配置文件，要检查当前服务是否保存到配置文件了
        if not os.path.exists(conf_file) or not os.path.exists(keyring_file):
            ceph.save()
            conf_file = ceph.config_file
            keyring_file = ceph.keyring_file

        try:
            rbd_manager = RbdManager(conf_file=conf_file, keyring_file=keyring_file, pool_name=pool_name)
            return rbd_manager
        except RadosError as e:
            raise VmError(msg=str(e))

    def _get_image(self, image_id:int):
        '''
        获取image

        :return:
            Image()
            raise VmError

        :raise VmError
        '''
        try:
            image = self._image_manager.get_image_by_id(image_id)
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

    def _get_host_list(self, vlan:Vlan, user, host_id=None, group_id=None):
        '''
        获取属于vlan子网的指定宿主机列表

        说明：group_id和host_id参数必须给定一个；host_id有效时，使用host_id；host_id无效时，使用group_id；

        :param vlan: 子网对象Vlan()
        :param host_id: 宿主机id，有效时只获取此宿主机
        :param group_id: 宿主机组id, host_id==None时，只获取此组的宿主机
        :return:
            list    # success
            raise VmError   # failed ,未找到宿主机或发生错误

        :raise VmError
        '''
        host_list = []
        if host_id:
            try:
                h = self._host_manager.get_host_by_id(host_id)
            except ComputeError as e:
                raise VmError(msg=str(e))

            # 用户访问宿主机权限检查
            if not h.user_has_perms(user=user):
                raise VmError(msg='当前用户没有指定宿主机的访问权限')

            # 宿主机存在, 并符合子网要求
            if h and h.contains_vlan(vlan):
                host_list.append(h)
        elif group_id:
            try:
                group = self._group_manager.get_group_by_id(group_id=group_id)
            except ComputeError as e:
                raise VmError(msg=f'查询宿主机组，{str(e)}')
            if not group:
                raise VmError(msg='指定宿主机组不存在')

            # 用户访问宿主机组权限检查
            if not group.user_has_perms(user=user):
                raise VmError(msg='当前用户没有指定宿主机的访问权限')

            try:
                host_list = self._host_manager.get_hosts_by_group_and_vlan(group_or_id=group_id, vlan=vlan)
            except ComputeError as e:
                raise VmError(msg=f'获取宿主机list错误，{str(e)}')
        if not host_list:
            raise VmError(msg='参数有误，未找到指定的可用宿主机')

        return host_list

    def _apply_for_macip(self, vlan:Vlan, ipv4=None):
        '''
        申请一个指定属于子网的mac ip

        :param vlan: 子网对象Vlan()
        :param ipv4: 指定要申请的ip
        :return:
            MacIP()    # success
            raise VmError   # failed ,未找到可用mac ip或发生错误

        :raise VmError
        '''
        if ipv4: # 如果指定了要使用的ip
            macip = self._macip_manager.apply_for_free_ip(vlan_id=vlan.id, ipv4=ipv4)
        else:
            macip = self._macip_manager.apply_for_free_ip(vlan_id=vlan.id)
        if not macip:
            raise VmError(msg='申请mac ip失败')

        return macip

    def _apply_for_host(self, hosts:list, vcpu:int, mem:int, claim=False):
        '''
        向宿主机申请资源

        :param hosts: 宿主机列表
        :param vcpu: 要申请的cpu数
        :param mem: 要申请的内存大小
        :param claim: True:立即申请资源
        :return:
            Host()    # success
            raise VmError   # failed ,未找到可用mac ip或发生错误

        :raise VmError
        '''
        try:
            host = self._host_manager.filter_meet_requirements(hosts=hosts, vcpu=vcpu, mem=mem, claim=True)
        except ComputeError as e:
            raise VmError(msg=f'无法创建虚拟机,{str(e)}')

        # 没有满足资源需求的宿主机
        if not host:
            raise VmError(msg='无法创建虚拟机,没有足够资源的宿主机可用')

        return host

    def create_vm(self, image_id:int, vcpu:int, mem:int, vlan_id:int, user, group_id=None, host_id=None, ipv4=None, remarks=None):
        '''
        创建一个虚拟机

        说明：group_id和host_id参数必须给定一个；host_id有效时，使用host_id；host_id无效时，使用group_id；
        备注：虚拟机的名称和系统盘名称同虚拟机的uuid

        :param image_id: 镜像id
        :param vcpu: cpu数
        :param mem: 内存大小
        :param vlan_id: 子网id
        :param group_id: 宿主机组id
        :param host_id: 宿主机id
        :param ipv4:  指定要创建的虚拟机ip
        :param remarks: 备注
        :return:
            Vm()
            raise VmError

        :raise VmError
        '''
        macip = None # 申请的macip
        host = None # 申请的宿主机
        diskname = None # clone的系统镜像
        vm = None # 虚拟机

        if vcpu <= 0: raise VmError(msg='无法创建虚拟机,vcpu参数无效')
        if mem <= 0: raise VmError(msg='无法创建虚拟机,men参数无效')

        image = self._get_image(image_id)    # 镜像
        vlan = self._get_vlan(vlan_id)      # 局域子网
        host_list = self._get_host_list(vlan=vlan, host_id=host_id, group_id=group_id, user=user) # 宿主机

        vm_uuid_obj = self.new_uuid_obj()
        vm_uuid = vm_uuid_obj.hex

        ceph_pool = image.ceph_pool
        pool_name = ceph_pool.pool_name
        ceph_config = ceph_pool.ceph
        rbd_manager = self.get_rbd_manager(ceph=ceph_config, pool_name=pool_name)

        try:
            macip = self._apply_for_macip(vlan=vlan, ipv4=ipv4)  # mac ip资源申请
            host = self._apply_for_host(hosts=host_list, vcpu=vcpu, mem=mem, claim=True)  # 向宿主机申请资源

            # 创建虚拟机的系统镜像disk
            try:
                rbd_manager.clone_image(snap_image_name=image.base_image, snap_name=image.snap, new_image_name=vm_uuid)
                diskname = vm_uuid
            except RadosError as e:
                raise VmError(msg=f'clone image error, {str(e)}')

            # 虚拟机xml
            xml_tpl = image.xml_tpl.xml  # 创建虚拟机的xml模板字符串
            xml_desc = xml_tpl.format(name=vm_uuid, uuid=vm_uuid, mem=mem, vcpu=vcpu, ceph_uuid=ceph_config.uuid,
                ceph_pool=pool_name, diskname=diskname, ceph_username=ceph_config.username,
                ceph_hosts_xml=ceph_config.hosts_xml, mac=macip.mac, bridge=vlan.br)

            # 创建虚拟机元数据
            vm = Vm(uuid=vm_uuid_obj, name=vm_uuid, vcpu=vcpu, mem=mem, disk=diskname, user=user,
                    remarks=remarks, host=host, mac_ip=macip,xml=xml_desc, image=image)
            vm.save()

            # 创建虚拟机
            try:
                self._vm_manager.define(host_ipv4=host.ipv4, xml_desc=xml_desc)
            except VirtError as e:
                raise VmError(msg=str(e))
            host.vm_created_num_add_1() # 宿主机已创建虚拟机数量+1
            return vm
        except Exception as e:
            if macip:
                self._macip_manager.free_used_ip(ip_id=macip.id)  # 释放已申请的mac ip资源
            if host:
                self._host_manager.free_to_host(host_id=host.id, vcpu=vcpu, mem=mem) # 释放已申请的宿主机资源
            if diskname:
                rbd_manager.remove_image(image_name=diskname)

            if vm:
                vm.delete()
            raise VmError(msg=str(e))

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
        vm = self._vm_manager.get_vm_by_uuid(vm_uuid=vm_uuid)
        if vm is None:
            raise VmError(msg='虚拟机不存在')
        if not vm.user_has_perms(user=user):
            raise VmError(msg='当前用户没有权限访问此虚拟机')

        host = vm.host
        # 虚拟机的状态
        try:
            run = self._vm_manager.is_running(host_ipv4=host.ipv4, vm_uuid=vm_uuid)
        except VirtError as e:
            raise VmError(msg='获取虚拟机运行状态失败')
        if run:
            if not force:
                raise VmError(msg='虚拟机正在运行，请先关闭虚拟机')
            try:
                self._vm_manager.poweroff(host_ipv4=host.ipv4, vm_uuid=vm_uuid)
            except VirtError as e:
                raise VmError(msg='强制关闭虚拟机失败')

        # 归档虚拟机
        try:
            vm_ahv = VmArchiveManager().add_vm_archive(vm)
        except VmError as e:
            raise VmError(msg=f'归档虚拟机失败，{str(e)}')

        log_manager = VmLogManager()

        # 删除虚拟机
        try:
            if not self._vm_manager.undefine(host_ipv4=host.ipv4, vm_uuid=vm_uuid):
                raise VmError(msg='删除虚拟机失败')
        except (VirtError, VmError):
            vm_ahv.delete()  # 删除归档记录
            raise VmError(msg='删除虚拟机失败')

        # 删除虚拟机元数据
        try:
            vm.delete()
        except Exception as e:
            msg = f'虚拟机（uuid={vm.get_uuid()}）已删除，并归档，但是虚拟机元数据删除失败;请手动删除虚拟机元数据。'
            log_manager.add_log(title='删除虚拟机元数据失败', about=log_manager.about.ABOUT_VM_METADATA, text=msg)
            raise VmError(msg='删除虚拟机元数据失败')

        # 宿主机已创建虚拟机数量-1
        if not host.vm_created_num_sub_1():
            msg = f'虚拟机（uuid={vm.get_uuid()}）已删除，并归档，宿主机（id={host.id}; ipv4={host.ipv4}）已创建虚拟机数量-1失败, 请手动-1。'
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

        vm = self._vm_manager.get_vm_by_uuid(vm_uuid=vm_uuid)
        if vm is None:
            raise VmError(msg='虚拟机不存在')
        if not vm.user_has_perms(user=user):
            raise VmError(msg='当前用户没有权限访问此虚拟机')

        # 没有变化直接返回
        if vm.vcpu == vcpu and vm.mem == mem:
            return True

        host = vm.host
        # 虚拟机的状态
        try:
            run = self._vm_manager.is_running(host_ipv4=host.ipv4, vm_uuid=vm_uuid)
        except VirtError as e:
            raise VmError(msg='获取虚拟机运行状态失败')
        if run:
            if not force:
                raise VmError(msg='虚拟机正在运行，请先关闭虚拟机')
            try:
                self._vm_manager.poweroff(host_ipv4=host.ipv4, vm_uuid=vm_uuid)
            except VirtError as e:
                raise VmError(msg='强制关闭虚拟机失败')

        xml_desc = self._vm_manager.get_vm_xml_desc(host_ipv4=host.ipv4, vm_uuid=vm_uuid)
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
            raise  VmError(msg='修改虚拟机元数据失败')

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
        vm = self._vm_manager.get_vm_by_uuid(vm_uuid=vm_uuid)
        if vm is None:
            raise VmError(msg='虚拟机不存在')
        if not vm.user_has_perms(user=user):
            raise VmError(msg='当前用户没有权限访问此虚拟机')

        host = vm.host
        host_ip = host.ipv4

        try:
            if op == 'start':
                return self._vm_manager.start(host_ipv4=host_ip, vm_uuid=vm_uuid)
            elif op == 'reboot':
                return self._vm_manager.reboot(host_ipv4=host_ip, vm_uuid=vm_uuid)
            elif op == 'shutdown':
                return self._vm_manager.shutdown(host_ipv4=host_ip, vm_uuid=vm_uuid)
            elif op == 'poweroff':
                return self._vm_manager.poweroff(host_ipv4=host_ip, vm_uuid=vm_uuid)
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
        vm = self._vm_manager.get_vm_by_uuid(vm_uuid=vm_uuid)
        if vm is None:
            raise VmError(msg='虚拟机不存在')
        if not vm.user_has_perms(user=user):
            raise VmError(msg='当前用户没有权限访问此虚拟机')

        host = vm.host
        host_ip = host.ipv4
        try:
            return self._vm_manager.domain_status(host_ipv4=host_ip, vm_uuid=vm_uuid)
        except VirtError as e:
            raise VmError(msg='获取虚拟机状态失败')

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
        vm = self._vm_manager.get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=())
        if vm is None:
            raise VmError(msg='虚拟机不存在')
        if not vm.user_has_perms(user=user):
            raise VmError(msg='当前用户没有权限访问此虚拟机')

        vm.remarks = remark
        try:
            vm.save(update_fields=['remarks'])
        except Exception as e:
            raise VmError(msg='更新备注信息失败')

        return True

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

        vm = self._vm_manager.get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=('user', 'host', 'host__group'))
        if vm is None:
            raise VmError(msg='虚拟机不存在')
        if not vm.user_has_perms(user=user):
            raise VmError(msg='当前用户没有权限访问此虚拟机')

        # 虚拟机的状态
        host = vm.host
        if host.group != vdisk.quota.group:
            raise VmError(msg='虚拟机和硬盘不再同一个机组')

        try:
            run = self._vm_manager.is_running(host_ipv4=host.ipv4, vm_uuid=vm_uuid)
        except VirtError as e:
            raise VmError(msg='获取虚拟机运行状态失败')
        if run:
            raise VmError(msg='虚拟机正在运行，请先关闭虚拟机')

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
            xml_desc = self._vm_manager.get_domain_xml_desc(vm_uuid=vm.get_uuid(), host_ipv4=vm.host.ipv4)
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
        try:
            run = self._vm_manager.is_running(host_ipv4=host.ipv4, vm_uuid=vm.hex_uuid)
        except VirtError as e:
            raise VmError(msg='获取虚拟机运行状态失败')
        if run:
            raise VmError(msg='虚拟机正在运行，请先关闭虚拟机')

        # 向虚拟机挂载硬盘
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
            xml_desc = self._vm_manager.get_domain_xml_desc(vm_uuid=vm.get_uuid(), host_ipv4=vm.host.ipv4)
            vm.xml = xml_desc
            vm.save(update_fields=['xml'])
        except Exception:
            pass

        return vdisk

