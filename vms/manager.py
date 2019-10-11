import uuid
import os

from django.db import transaction
from django.db.models import F, Q

from utils.ceph.manages import RadosError, RbdManager
from .virt import VirtAPI
from .models import (Center, Group, Host, Vm, Image, MacIP, Vlan, CephCluster)
from . import errors
from .errors import VmError

class VirtualMachine(VirtAPI):
    '''

    '''
    def __init__(self, vm:Vm):
        pass

class CenterManager:
    '''
    分中心管理器
    '''
    def get_center_by_id(self, center_id:int):
        '''
        通过id获取分中心

        :param center_id: 分中心id
        :return:
            Image() # success
            None    #不存在
        :raise VmError
        '''
        if not isinstance(center_id, int) or center_id < 0:
            raise VmError(code=errors.ERR_CENTER_ID, msg='分中心ID参数有误')

        try:
            return Center.objects.filter(id=center_id).first()
        except Exception as e:
            raise VmError(msg=f'查询分中心时错误,{str(e)}')


class GroupManager:
    '''
    宿主机组管理器
    '''
    def get_group_by_id(self, group_id:int):
        '''
        通过id获取宿主机组

        :param group_id: 宿主机组id
        :return:
            Group() # success
            None    #不存在
        :raise VmError
        '''
        if not isinstance(group_id, int) or group_id < 0:
            raise VmError(code=errors.ERR_GROUP_ID, msg='宿主机组ID参数有误')

        try:
            return Group.objects.filter(id=group_id).first()
        except Exception as e:
            raise VmError(msg=f'查询宿主机组时错误,{str(e)}')


class HostManager:
    '''
    宿主机管理器
    '''
    def get_host_by_id(self, host_id:int):
        '''
        通过id获取宿主机元数据模型对象

        :param host_id: 宿主机id
        :return:
            Host() # success
            None    #不存在
        :raise VmError
        '''
        if not isinstance(host_id, int) or host_id < 0:
            raise VmError(code=errors.ERR_HOST_ID, msg='宿主机ID参数有误')

        try:
            return Host.objects.filter(id=host_id).first()
        except Exception as e:
            raise VmError(msg=f'查询宿主机时错误,{str(e)}')

    def get_hosts_by_group_id(self, group_id:int):
        '''
        获取宿主机组的所有宿主机元数据模型对象

        :param group_id: 宿主机组id
        :return:
            [Host(),]    # success
            raise VmError #发生错误

        :raise VmError
        '''
        if not isinstance(group_id, int) or group_id < 0:
            raise VmError(code=errors.ERR_GROUP_ID, msg='宿主机组ID参数有误')
        try:
            hosts_qs = Host.objects.filter(group=group_id).all()
            return list(hosts_qs)
        except Exception as e:
            raise VmError(msg=f'查询宿主机组的宿主机列表时错误,{str(e)}')

    def get_hosts_by_group_and_vlan(self, group_or_id, vlan:Vlan):
        '''
        获取宿指定主机组，并且包含指定vlan的所有宿主机元数据模型对象

        :param group_or_id: 宿主机组对象Group()或id
        :param vlan: 子网对象
        :return:
            [Host(),]    # success
            raise VmError #发生错误

        :raise VmError
        '''
        if isinstance(group_or_id, Group):
            group = group_or_id
        elif isinstance(group_or_id, int) and group_or_id > 0:
            group = group_or_id
        else:
            raise VmError(msg='请输入一个宿主机组对象或宿主机组ID')

        if not isinstance(vlan, Vlan):
            raise VmError(msg='请输入一个子网Vlan对象')

        try:
            hosts_qs = vlan.vlan_hosts.filter(group=group).all()
            return list(hosts_qs)
        except Exception as e:
            raise VmError(msg=f'查询宿主机组的宿主机列表时错误,{str(e)}')


    def claim_from_host(self, host_id:int, vcpu:int, mem:int):
        '''
        向宿主机申请资源

        :param host_id: 宿主机id
        :param vcpu: 要申请的cpu数
        :param mem: 要申请的内存大小
        :return:
            Host()  # success
            None    #宿主机不存在，或没有足够的资源
        :raise VmError
        '''
        with transaction.atomic():
            host = Host.objects.select_for_update().filter(id=host_id).first()
            if not host:
                return None

            # 宿主机是否满足资源需求
            if not host.meet_needs(vcpu=vcpu, mem=mem):
                raise VmError(msg='宿主机没有足够的资源')

            # 申请资源
            if not host.claim(vcpu=vcpu, mem=mem):
                raise VmError(msg='向宿主机申请资源时失败')

        return host

    def free_to_host(self, host_id: int, vcpu: int, mem: int):
        '''
        释放从宿主机申请的资源

        :param host_id: 宿主机id
        :param vcpu: 要申请的cpu数
        :param mem: 要申请的内存大小
        :return:
            True    # success
            False   # failed
        '''
        # 释放资源
        host = Host.objects.filter(id=host_id).first()
        if not host:
            return False

        return host.free(vcpu=vcpu, mem=mem)

    def filter_meet_requirements(self, hosts:list, vcpu:int, mem:int, claim=False):
        '''
        筛选满足申请资源要求的宿主机

        :param hosts: 宿主机列表
        :param vcpu: 要申请的cpu数
        :param mem: 要申请的内存大小
        :param claim: True:立即申请资源
        :return:
            Host()  # success
            None    # 没有足够的资源的宿主机

        :raise VmError
        '''
        # 检查参数
        if not isinstance(hosts, list):
            raise VmError(msg='参数有误，请输入宿主机列表')

        if len(hosts) == 0: # 没有满足条件的宿主机
            return None

        if not isinstance(hosts[0], Host):
            raise VmError(msg='参数有误，请输入宿主机列表')

        if not isinstance(vcpu, int) or vcpu <= 0:
            raise VmError(msg='参数有误，vcpu必须是一个正整数')

        if not isinstance(mem, int) or mem <= 0:
            raise VmError(msg='参数有误，mem必须是一个正整数')

        for host in hosts:
            # 宿主机是否满足资源需求
            if not host.meet_needs(vcpu=vcpu, mem=mem):
                continue

            if not claim: # 立即申请资源
                continue

            try:
                host = self.claim_from_host(host_id=host.id, vcpu=vcpu, mem=mem)
            except VmError as e:
                raise e

            if host:
                return host

        return None


class ImageManager:
    '''
    镜像管理器
    '''
    def get_image_by_id(self, image_id:int):
        '''
        通过id获取镜像元数据模型对象
        :param image_id: 镜像id
        :return:
            Image() # success
            None    #不存在

        :raise VmError
        '''
        if not isinstance(image_id, int) or image_id < 0:
            raise VmError(code=errors.ERR_IMAGE_ID, msg='镜像ID参数有误')

        try:
            return Image.objects.filter(id=image_id).first()
        except Exception as e:
            raise VmError(msg=f'查询镜像时错误,{str(e)}')


class VlanManager:
    '''
    局域子网Vlan管理器
    '''
    def get_vlan_by_id(self, vlan_id:int):
        '''
        通过id获取镜像元数据模型对象
        :param vlan_id: 镜像id
        :return:
            Vlan() # success
            None    #不存在

        :raise VmError
        '''
        if not isinstance(vlan_id, int) or vlan_id < 0:
            raise VmError(code=errors.ERR_VLAN_ID, msg='子网ID参数有误')

        try:
            return Vlan.objects.filter(id=vlan_id).first()
        except Exception as e:
            raise VmError(msg=f'查询镜像时错误,{str(e)}')


class MacIPManager:
    '''
    mac ip地址管理器
    '''
    def get_macip_by_id(self, macip_id:int):
        '''
        通过id获取mac ip

        :param macip_id: mac ip id
        :return:
            MacIP() # success
            None    #不存在

        :raise VmError
        '''
        if not isinstance(macip_id, int) or macip_id < 0:
            raise VmError(code=errors.ERR_MACIP_ID, msg='MacIP ID参数有误')

        try:
            return MacIP.objects.filter(id=macip_id).first()
        except Exception as e:
            raise VmError(msg=f'查询MacIP时错误,{str(e)}')

    def has_free_ip_in_vlan(self, vlan_id:int):
        '''
        子网中是否有可用的IP

        :param vlan_id: 子网id
        :return:
            True: 有
            False: 没有
        '''
        qs = MacIP.get_all_free_ip_in_vlan(vlan_id)
        if qs.count() > 0:
            return True

        return False

    def apply_for_free_ip(self, vlan_id:int, ipv4:str=''):
        '''
        申请一个未使用的ip，申请成功的ip不再使用时需要通过free_used_ip()释放

        :param vlan_id: 子网id
        :param ipv4: 指定要申请的ip
        :return:
            MacIP() # 成功
            None    # 失败
        '''
        with transaction.atomic():
            qs_ips = MacIP.objects.select_for_update().filter(vlan=vlan_id, used=False, enable=True)
            if ipv4:
                qs_ips = qs_ips.filter(ipv4=ipv4)

            ip = qs_ips.first()
            if not ip:
                return None

            ip.used = True
            ip.save()

        return ip

    def free_used_ip(self, ip_id:int=0, ipv4:str=''):
        '''
        释放一个使用中的ip,通过id或ip

        :param ip_id:
        :param ipv1:
        :return:
            True    # success
            False   # failed
        '''
        with transaction.atomic():
            if ip_id > 0:
                ip = MacIP.objects.select_for_update().filter(id=ip_id).first()
            elif ipv4:
                ip = MacIP.objects.select_for_update().filter(ipv4=ipv4).first()
            else:
                return False

            if not ip:
                return False

            if not ip.set_free():
                return False

        return True



class VmManager(VirtAPI):
    '''
    虚拟机元数据管理器
    '''

    def get_vm_by_uuid(self, uuid:str):
        '''
        通过uuid获取虚拟机元数据

        :param uuid: 虚拟机uuid hex字符串
        :return:
            Vm() # success
            None    #不存在或发生错误
        '''
        try:
            return Vm.objects.filter(uuid=uuid).first()
        except Exception as e:
            pass

        return None

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
        return Vm.objects.filter(user=user).all()




class VmAPI:
    '''
    虚拟机API
    '''
    def __init__(self):
        self._center_manager = CenterManager()
        self._group_manager = GroupManager()
        self._host_manager = HostManager()
        self._vm_manager = VmManager()
        self._image_manager = ImageManager()
        self._vlan_manager = VlanManager()
        self._macip_manager = MacIPManager()

    def new_uuid_str(self):
        '''
        生成一个新的uuid字符串
        :return: uuid:str
        '''
        return uuid.uuid4().hex

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
        except VmError as e:
            raise e
        if not image:
            raise VmError(code=errors.ERR_IMAGE_ID, msg='镜像ID参数有误，未找到指定系统镜像')
        if not image.enable:
            raise VmError(code=errors.ERR_IMAGE_ID, msg='镜像ID参数有误，镜像未启用')

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
        except VmError as e:
            raise e

        if not vlan:
            raise VmError(code=errors.ERR_VLAN_ID, msg='子网ID有误，子网不存在')

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
            except VmError as e:
                raise e
            # 用户访问宿主机权限检查
            if not h.user_has_perms(user=user):
                raise VmError(msg='当前用户没有指定宿主机的访问权限')
            # 宿主机存在, 并符合子网要求
            if h and h.contains_vlan(vlan):
                host_list.append(h)
        elif group_id:
            group = self._group_manager.get_group_by_id(group_id=group_id)
            if not group:
                raise VmError(msg='指定宿主机组不存在')
            # 用户访问宿主机组权限检查
            if not group.user_has_perms(user=user):
                raise VmError(msg='当前用户没有指定宿主机的访问权限')
            try:
                host_list = self._host_manager.get_hosts_by_group_and_vlan(group_or_id=group_id, vlan=vlan)
            except VmError as e:
                raise e
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
        except VmError as e:
            raise VmError(code=e.code, msg='无法创建虚拟机,' + e.detail())

        # 没有满足资源需求的宿主机
        if not host:
            raise VmError(msg='无法创建虚拟机,没有足够资源的宿主机可用')

        return host

    def create_vm(self, image_id:int, vcpu:int, mem:int, vlan_id:int, user, group_id=None, host_id=None, ipv4=None, remarks=None):
        '''
        创建一个虚拟机

        说明：group_id和host_id参数必须给定一个；host_id有效时，使用host_id；host_id无效时，使用group_id；

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

        vm_uuid = self.new_uuid_str()
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
            vm = Vm(uuid=vm_uuid, name=vm_uuid, vcpu=vcpu, mem=mem, disk=diskname, user=user,
                    remarks=remarks, host=host, mac_ip=macip,xml=xml_desc, image=image)
            vm.save()

            # 创建虚拟机
            try:
                self._vm_manager.define(host_ipv4=host.ipv4, xml_desc=xml_desc)
            except VmError as e:
                raise  e
            host.vm_created += 1
            host.save()
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
        :param force:   是否强制删除
        :return:
            True
            raise VmError

        :raise VmError
        '''
        vm = self._vm_manager.get_vm_by_uuid(uuid=vm_uuid)
        if vm is None:
            raise VmError(msg='虚拟机不存在')
        if not vm.user_has_perms(user=user):
            raise VmError(msg='当前用户没有权限访问此虚拟机')

        host = vm.host
        # 虚拟机的状态
        try:
            run = self._vm_manager.is_running(host_ipv4=host.ipv4, vm_uuid=vm_uuid)
        except VmError as e:
            raise VmError(msg='获取虚拟机运行状态失败')
        if run:
            if not force:
                raise VmError(msg='虚拟机正在运行，请先关闭虚拟机')
            try:
                self._vm_manager.poweroff(host_ipv4=host.ipv4, vm_uuid=vm_uuid)
            except VmError as e:
                raise VmError(msg='强制关闭虚拟机失败')

        try:
            # 释放mac ip
            mac_ip = vm.mac_ip
            if not mac_ip.set_free():
                raise VmError(msg='释放mac ip资源失败')

            # 释放disk
            if not vm.rm_sys_disk():
                raise VmError(msg='删除系统盘失败')

            # 释放宿主机资源
            if not host.free(vcpu=vm.vcpu, mem=vm.mem):
                raise VmError(msg='释放宿主机资源失败')

            # 删除虚拟机
            if not self._vm_manager.undefine(host_ipv4=host.ipv4, vm_uuid=vm_uuid):
                raise VmError(msg='删除虚拟机失败')

        except VmError as e:
            if not force:   # 非强制删除
                raise e

        try:
            vm.delete()
        except Exception as e:
            raise  VmError(msg='删除虚拟机元数据失败')

        return True


