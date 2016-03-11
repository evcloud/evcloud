#coding=utf-8
from .models import Center as DBCenter
from .models import Group as DBGroup
from .models import Vm as DBVm
from .models import Host as DBHost
from .center import Center
from .group import Group
from vmuser.api import API as UserAPI
from .vm.vm import VM

from api.error import Error
from api.error import ERR_VM_ID
from api.error import ERR_HOST_ID
from api.error import ERR_HOST_IPV4
from api.error import ERR_GROUP_ID
from .host.manager import HostManager
from .host.host import Host

from network.api import NetworkAPI
from image.api import ImageAPI
from .vm.manager import VMManager
from api.error import ERR_VM_CREATE_ARGS_VLAN
from api.error import ERR_VM_CREATE_ARGS_HOST
from api.error import ERR_VM_HOST_FILTER
from api.error import ERR_VM_CREATE_DB
from api.error import ERR_VM_CREATE_DISK
from api.error import ERR_VM_VCPU
from api.error import ERR_VM_MEM
from api.error import ERR_VM_RESET_LIVING
from api.error import ERR_VM_EDIT_LIVING
from api.error import ERR_VM_MIGRATE_LIVING
from api.error import ERR_VM_DEL_GPU_MOUNTED
from api.error import ERR_VM_DEL_VOL_MOUNTED

from django.conf import settings



class CenterAPI(object):

    def center_id_exists(self, center_id):
        return DBCenter.objects.filter(pk=center_id).exists()

    def get_center_by_id(self, center_id):
        center = DBCenter.objects.filter(id = center_id)
        if not center.exists():
            return False
        center = center[0]
        return self._get_center_data(center)

    def get_center_list(self):
        centers = DBCenter.objects.all().order_by('order')
        ret_list = []
        for center in centers:
            ret_list.append(self._get_center_data(center))
        return ret_list

    def get_center_list_in_perm(self, user):
        centers = DBCenter.objects.all().order_by('order')
        ret_list = []
        for center in centers:
            c = self._get_center_data(center)
            if c.managed_by(user):
                ret_list.append(c)
        return ret_list        

    def _get_center_data(self, center):
        if type(center) != DBCenter:
            return False
        return Center(center)


class GroupAPI(object):

    def __init__(self, user_api=None):
        if not user_api:
            self.user_api = UserAPI()
        else:
            self.user_api = user_api

    def get_group_list_in_perm(self, username, center_id = None):
        user = self.user_api.get_db_user_by_username(username)
        if self.user_api.is_superuser(user):
            if center_id == None:
                groups = DBGroup.objects.all()
            else:
                groups = DBGroup.objects.filter(center_id = center_id)
        else:
            if center_id == None:
                groups = DBGroup.objects.filter(admin_user = user)
            else:
                groups = DBGroup.objects.filter(admin_user = user, center_id = center_id)
        groups = groups.order_by('order')
        ret_list = []
        for group in groups:
            ret_list.append(self._get_group_data(group))
        return ret_list

    def get_group_list(self, center_id = None):
        if center_id == None:
            groups = DBGroup.objects.filter()
        else:
            groups = DBGroup.objects.filter(center_id = center_id)
        groups = groups.order_by('order')
        ret_list = []
        for group in groups:
            ret_list.append(self._get_group_data(group))
        return ret_list

    def get_group_by_id(self, group_id):
        group = DBGroup.objects.filter(id = group_id)
        if not group.exists():
            raise Error(ERR_GROUP_ID)
        return self._get_group_data(group[0])

            
    def has_center_perm(self, username, center_id):
        user = self.user_api.get_db_user_by_username(username)
        '''对指定center有部分或全部管理权，即对该分中心中的 某个集群有管理权,则返回True'''
        return DBGroup.objects.filter(admin_user = user, center_id = center_id).exists()


    #--------------------------------------------------------
    def _get_group_data(self, group):
        if not type(group) == DBGroup:
            return False
        return Group(group)

class VmAPI(object):
    def __init__(self, manager=None, user_api=None, network_api=None, image_api=None, group_api=None, host_api=None):
        if not manager:
            self.manager = VMManager()
        else:
            self.manager = manager
        if not user_api:
            self.user_api = UserAPI()
        else:
            self.user_api = user_api
        if not network_api:
            self.network_api = NetworkAPI()
        else:
            self.network_api = network_api
        if not image_api:
            self.image_api = ImageAPI()
        else:
            self.image_api = image_api
        if not group_api:
            self.group_api = GroupAPI()
        else:
            self.group_api = group_api
        if not host_api:
            self.host_api = HostAPI()
        else:
            self.host_api = host_api

    def get_vm_by_uuid(self, vm_uuid):
        return self.manager.get_vm_by_uuid(vm_uuid)

    def get_vm_list_by_group_id(self, group_id, host_id=None, order=None):
        return self.manager.get_vm_list_by_group_id(group_id, host_id, order)

    def vm_uuid_exists(self, vm_uuid):
        return self.manager.vm_uuid_exists(vm_uuid)
        
    def attach_device(self, vm_uuid, xml):
        vm = self.manager.get_vm_by_uuid(vm_uuid)
        return vm.attach_device(xml)

    def detach_device(self, vm_uuid, xml):
        vm = self.manager.get_vm_by_uuid(vm_uuid)
        return vm.detach_device(xml)  

    def set_creator(self, vm_uuid, username):
        vm = self.manager.get_vm_by_uuid(vm_uuid)
        return vm.set_creator(str(username))

    def create_vm(self, image_id, vcpu, mem, group_id=None, host_id=None,
        net_type_id=None, vlan_id=None, diskname=None, vm_uuid=None, remarks=None):
        '''
        参数说明：
            image_id, vcpu, mem 为必要参数。
            group_id, host_id 两者至少必须有其一, host_id存在时指定相应宿主机，
            无host_id但有group_id时在指定集群筛选宿主机。
            net_type_id, vlan_id 两者至少必须有其一，有vlan_id时使用指定的网段，
            无vlan_id但有net_type_id时在指定网络类型中筛选网段。
            其他参数都是可选参数。
        '''
        vcpu = int(vcpu)
        mem = int(mem)

        if not vm_uuid:
            vm_uuid = self.manager.create_vm_uuid()
        if not diskname:
            diskname = vm_uuid

        image_info = self.image_api.get_image_info_by_id(image_id)

        if host_id:
            host_list = [self.host_api.get_host_by_id(host_id)]
        elif group_id:
            host_list = self.host_api.get_host_list_by_group_id(group_id)
        else:
            raise Error(ERR_VM_CREATE_ARGS_HOST)   
        
        available_host_list = []
        for host in host_list:
            if not host.exceed_vm_limit() and not host.exceed_mem_limit(mem):
                available_host_list.append(host)
        
        if  settings.DEBUG: print('[create_vm]', '可用主机列表', available_host_list)

        if vlan_id:
            vlan_list = [self.network_api.get_vlan_by_id(vlan_id)]
        elif net_type_id:
            vlan_list = self.network_api.get_vlan_list_by_type_id(net_type_id)
        else:
            raise Error(ERR_VM_CREATE_ARGS_VLAN)

        if settings.DEBUG: print('[create_vm]', '网段列表', vlan_list)

        while available_host_list:
            mac_claimed = False
            disk_created = False
        
            host = self.host_api.host_filter(available_host_list, vcpu, mem, claim=True)  
            if not host:
                raise Error(ERR_VM_HOST_FILTER)
            available_host_list.remove(host)

            if host.alive():
                host_available_vlan_id_list = self.host_api.get_vlan_id_list_of_host(host.id)
                for vlan in vlan_list:
                    try:
                        if not vlan.id in host_available_vlan_id_list:
                            continue
                        if settings.DEBUG: print('[create_vm]', '开始创建', host, vlan)
                        mac_claimed = False
                        disk_created = False

                        mac = self.network_api.mac_claim(vlan.id, vm_uuid)
                        if mac:
                            mac_claimed = True
                        
                        if mac_claimed:
                            if self.image_api.init_disk(image_id, diskname):
                                disk_created = True
                            else:
                                raise Error(ERR_VM_CREATE_DISK)
                            image_info = self.image_api.get_image_info_by_id(image_id)

                            xml_tpl = self.image_api.get_xml_tpl(image_id)
                            xml_desc = xml_tpl % {
                                'name': vm_uuid,
                                'uuid': vm_uuid,
                                'mem': mem,
                                'vcpu': vcpu,
                                'ceph_uuid': image_info['ceph_uuid'],
                                'ceph_pool': image_info['ceph_pool'],
                                'diskname': diskname,
                                'ceph_host': image_info['ceph_host'],
                                'ceph_port': image_info['ceph_port'],
                                'ceph_username': image_info['ceph_username'],
                                'mac': mac,
                                'bridge': vlan.br
                            }

                            net_info = self.network_api.get_net_info_by_vmuuid(vm_uuid)

                            db = self.manager.create_vm_db({
                                'host_id': host.id,
                                'image_id': image_id,
                                'image_snap': image_info['image_snap'],
                                'image': image_info['image_name'],
                                'uuid': vm_uuid,
                                'name': vm_uuid,
                                'mem': mem,
                                'vcpu': vcpu,
                                'disk': diskname,
                                'remarks': remarks,
                                'ceph_id': image_info['ceph_id'],
                                'ceph_host': image_info['ceph_host'],
                                'ceph_pool': image_info['ceph_pool'],
                                'ceph_uuid': image_info['ceph_uuid'],
                                'ceph_port': image_info['ceph_port'],
                                'ceph_username': image_info['ceph_username'],
                                'vlan_id': net_info['vlan_id'],
                                'vlan_name': net_info['vlan_name'],
                                'ipv4': net_info['ipv4'],
                                'mac': net_info['mac'],
                                'br': net_info['br']
                                })

                            if db:
                                dom = self.manager.define(host.ipv4, xml_desc)                    
                                return VM(db)
                            else:
                                raise Error(ERR_VM_CREATE_DB)
                    except Error as e:
                        if settings.DEBUG: print('[create_vm]', '创建失败','mac_claimed', mac_claimed, 
                            'disk_created', disk_created)
                        if mac_claimed:
                            mac_released = self.network_api.mac_release(mac, vm_uuid)
                            if settings.DEBUG: print('[create_vm]', 'IP地址释放', mac_released)
                        if disk_created:
                            disk_deleted = self.image_api.rm_disk(image_id, diskname)
                            if settings.DEBUG: print('[create_vm]', '磁盘释放', disk_deleted)
                        if settings.DEBUG: print(e)
                        raise e
                    except Exception as e:
                        if settings.DEBUG: print('[create_vm]', '创建失败', 'mac_claimed', mac_claimed, 
                            'disk_created', disk_created)
                        
                        if mac_claimed:
                            mac_released = self.network_api.mac_release(mac, vm_uuid)
                            if settings.DEBUG: print('[create_vm]', 'IP地址释放', mac_released)
                        if disk_created:
                            disk_deleted = self.image_api.rm_disk(image_id, diskname)
                            if settings.DEBUG: print('[create_vm]', '磁盘释放', disk_deleted)
                        if settings.DEBUG: print(e)
            
            host_released = self.host_api.host_release(host, vcpu, mem)
            if settings.DEBUG: print('[create_vm]', '释放宿主机资源', host_released)
        return False
    
    def delete_vm(self, vm_uuid):
        vm = self.manager.get_vm_by_uuid(vm_uuid)
        image_id = vm.image_id
        diskname = vm.disk
        host_id = vm.host_id
        vcpu = vm.vcpu
        mem = vm.mem
        mac = vm.mac
        
        from device.api import GPUAPI
        from volume.api import CephVolumeAPI
        
        gpuapi = GPUAPI()
        if len(gpuapi.get_gpu_list_by_vm_uuid(vm_uuid)) > 0:
            raise Error(ERR_VM_DEL_GPU_MOUNTED)

        volumeapi = CephVolumeAPI()
        if len(volumeapi.get_volume_list_by_vm_uuid(vm_uuid)) > 0:
            raise Error(ERR_VM_DEL_VOL_MOUNTED)

        deletion_permitted = False



        archive_disk_name = ''
        if self.image_api.disk_exists(image_id, diskname):
            archive_disk_name = self.image_api.archive_disk(image_id, diskname)
            if archive_disk_name != False:
                deletion_permitted = True
        else:
            deletion_permitted = True
        if deletion_permitted:
            if vm.delete(archive_disk_name):
                if not self.host_api.host_release(host_id, vcpu, mem):
                    print('[delete_vm]', '释放宿主机资源失败')
                if not self.network_api.mac_release(mac, vm_uuid):
                    print('[delete_vm]', '释放IP地址失败')
                return True
        return False

    def reset_vm(self, vm_uuid):
        vm = self.manager.get_vm_by_uuid(vm_uuid)
        if vm.is_running():
            raise Error(ERR_VM_RESET_LIVING)
        archive_disk_name = self.image_api.archive_disk(vm.image_id, vm.disk)
        if archive_disk_name != False:
            init_disk_success = self.image_api.init_disk(vm.image_id, vm.disk)
            if init_disk_success:
                if vm.start():
                    return True
                self.image_api.rm_disk(vm.image_id, vm.disk)
            self.image_api.restore_disk(vm.image_id, archive_disk_name)
        return False 

    def edit_vm(self, vm_uuid, vcpu=None, mem=None, remarks=None):
        vm = self.get_vm_by_uuid(vm_uuid)

        if (vcpu != None or mem != None) and vm.is_running():
            raise Error(ERR_VM_EDIT_LIVING)
        
        if vcpu and not type(vcpu) == int:
            raise Error(ERR_VM_VCPU)

        if mem and not type(mem) == int:
            raise Error(ERR_VM_MEM)

        failed = False
        org_remarks = vm.remarks
        org_vcpu = vm.vcpu
        org_mem = vm.mem

        if not failed and remarks:
            if not vm.set_remarks(remarks):
                failed = True

        if not failed and vcpu:
            if vcpu > vm.vcpu:
                vcpu_claimed = self.host_api.host_claim(vm.host_id, vcpu - vm.vcpu, 0, 0)
            else:
                vcpu_claimed = self.host_api.host_release(vm.host_id, vm.vcpu - vcpu, 0, 0)
        else:
            vcpu_claimed = True

        if not failed and mem:
            if mem > vm.mem:
                mem_claimed = self.host_api.host_claim(vm.host_id, 0, mem - vm.mem, 0)
            else:
                mem_claimed = self.host_api.host_release(vm.host_id, 0, vm.mem - mem, 0)
        else:
            mem_claimed = True

        if not failed and vcpu_claimed and mem_claimed:
            if not self.manager.set_vm_configuration(vm_uuid, vcpu, mem):
                failed = True

        if failed:
            if remarks:
                vm.set_remarks(org_remarks)
            if vcpu or mem:
                self.manager.set_vm_configuration(vm_uuid, org_vcpu, org_mem)
                if vcpu and vcpu_claimed:
                    if vcpu > org_vcpu:
                        self.host_api.host_release(vm.host_id, vcpu - org_vcpu, 0, 0)
                    else:
                        self.host_api.host_claim(vm.host_id, org_vcpu - vcpu, 0, 0)
                if mem and mem_claimed:
                    if mem > org_mem:
                        self.host_api.host_release(vm.host_id, 0, mem - org_mem, 0)
                    else:
                        self.host_api.host_claim(vm.host_id, 0, org_mem - mem, 0)

            return False

        return True

    def migrate_vm(self, vm_uuid, host_id):
        #参数验证
        vm = self.manager.get_vm_by_uuid(vm_uuid)
        host = self.host_api.get_host_by_id(host_id)

        #判断是否在同一个center
        if vm.center_id != host.center_id:
            raise Error(ERR_VM_MIGRATE_DIFF_CEPH)

        #是否关机
        if vm.is_running():
            raise Error(ERR_VM_MIGRATE_LIVING)

        #在新宿主机上创建
        image_info = self.image_api.get_image_info_by_id(vm.image_id)

        xml_tpl = self.image_api.get_xml_tpl(vm.image_id)
        xml_desc = xml_tpl % {
            'name': vm_uuid,
            'uuid': vm_uuid,
            'mem': vm.mem,
            'vcpu': vm.vcpu,
            'ceph_uuid': image_info['ceph_uuid'],
            'ceph_pool': image_info['ceph_pool'],
            'diskname': vm.disk,
            'ceph_host': image_info['ceph_host'],
            'ceph_port': image_info['ceph_port'],
            'ceph_username': image_info['ceph_username'],
            'mac': vm.mac,
            'bridge': vm.br
        }

        if self.host_api.host_claim(host_id, vm.vcpu, vm.mem, 1):
            try:
                old_host_id = vm.host_id
                if self.manager.migrate(vm_uuid, host_id, host.ipv4, xml_desc):
                    self.host_api.host_release(old_host_id, vm.vcpu, vm.mem, 1)
                    return True 
            except Exception as e:
                self.host_api.host_release(host_id, vm.vcpu, vm.mem, 1)
                if type(e) == Error:
                    raise e
            else:
                self.host_api.host_release(host_id, vm.vcpu, vm.mem, 1)

        return False


class HostAPI(object):
    def __init__(self, user_api=None, manager=None):
        if not user_api:
            self.user_api = UserAPI()
        else:
            self.user_api = user_api
        if not manager:
            self.manager = HostManager()
        else:
            self.manager = manager

    def get_host_by_id(self, host_id):
        db = DBHost.objects.filter(id = host_id)
        if not db.exists():
            raise Error(ERR_HOST_ID)
        return Host(db[0])

    def get_host_by_ipv4(self, host_ipv4):
        db = DBHost.objects.filter(ipv4 = host_ipv4)
        if not db.exists():
            raise Error(ERR_HOST_IPV4)
        return Host(db[0])

    def get_pci_device_list_from_host(self, host_ip):
        host = self.get_host_by_ipv4(host_ip)
        return host.get_pci_device_list()

    def get_vlan_id_list_of_host(self, host_id):
        host = DBHost.objects.filter(id = host_id)
        if not host.exists():
            raise Error(ERR_HOST_ID)
        return [v.id for v in host[0].vlan.all()]

    def host_alive(self, host_ip):
        '''主机是否能ping通'''
        return self.manager.host_alive(host_ip)

    def host_filter(self, hosts, vcpu, mem, claim=True):
        '''返回最适合创建新虚拟机的宿主机。claim != True 时不申请资源，仅返回最佳主机。'''
        return self.manager.filter(hosts, vcpu, mem, claim)

    def host_claim(self, host, vcpu, mem, vm_num = 1):
        '''从指定宿主机申请资源'''
        return self.manager.claim(host, vcpu, mem, vm_num)

    def host_release(self, host, vcpu, mem, vm_num = 1):
        '''从指定宿主机释放资源'''
        return self.manager.release(host, vcpu, mem, vm_num)

    def get_host(self, host):
        '''将宿主机ID、宿主机IP地址、宿主机model对象转换成VMHost对象。不能转换则返回False'''
        return self.manager.check_host(host)

    def get_host_list_by_group_id(self, group_id):
        hosts = DBHost.objects.filter(group_id = group_id)
        ret_list = []
        for host in hosts:
            ret_list.append(Host(host))
        return ret_list
    