#coding=utf-8
from django.conf import settings
from vmuser.models import User
from vmuser.api import API as UserAPI
from network.api import NetworkAPI
from image.api import ImageAPI

from api.error import *

from .vm.vm import VM
from .vm.manager import VMManager

from .manager import CenterManager
from .manager import GroupManager
from .host.manager import HostManager

class CenterAPI(object):
    def __init__(self, manager=None):
        if not manager:
            self.manager = CenterManager()
        else:
            self.manager = manager

    def center_id_exists(self, center_id):
        return self.manager.center_id_exists(center_id)

    def get_center_by_id(self, center_id):
        return self.manager.get_center_by_id(center_id)

    def get_center_list(self):
        return self.manager.get_center_list()

    def get_center_list_in_perm(self, user):
        return self.manager.get_center_list_in_perm(user)


class GroupAPI(object):
    def __init__(self, manager=None, user_api=None):
        if not user_api:
            self.user_api = UserAPI()
        else:
            self.user_api = user_api
        if not manager:
            self.manager = GroupManager()
        else:
            self.manager = manager

    def get_group_list_in_perm(self, username, center_id = None):
        user = self.user_api.get_db_user_by_username(username)
        if self.user_api.is_superuser(user):
            return self.manager.get_group_list(center_id)
        else:
            return self.manager.get_group_list_by_user(user, center_id)

    def get_group_list(self, center_id = None):
        return self.manager.get_group_list(center_id)

    def get_group_by_id(self, group_id):
        return self.manager.get_group_by_id(group_id)

    def has_center_perm(self, username, center_id):

        if not isinstance(username, User) and type(username) is str:
            user = self.user_api.get_db_user_by_username(username)
        else:
            user = username
        '''对指定center有部分或全部管理权，即对该分中心中的 某个集群有管理权,则返回True'''
        return self.manager.has_center_perm(user, center_id)


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

    def get_vm_list_by_group_id(self, group_id, host_id=None, order=None,ha_monitored=None):
        return self.manager.get_vm_list_by_group_id(group_id, host_id, order, ha_monitored)   

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

    def set_ha_monitored(self, vm_uuid, ha_monitored=True):
        '''设置虚拟机的[高可用]属性'''
        vm = self.manager.get_vm_by_uuid(vm_uuid)
        return vm.set_ha_monitored(ha_monitored)

    def create_vm(self, image_id, vcpu, mem, group_id=None, host_id=None,
        net_type_id=None, vlan_id=None, diskname=None, vm_uuid=None, remarks=None, ipv4=None):
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

        image = self.image_api.get_image_by_id(image_id)
        if not image.enable:
            raise Error(ERR_IMAGE_ID)

        image_info = self.image_api.get_image_info_by_id(image_id)

        if host_id:
            host_list = [self.host_api.get_host_by_id(host_id)]
        elif group_id:
            host_list = self.host_api.get_host_list_by_group_id(group_id)
        else:
            raise Error(ERR_VM_CREATE_ARGS_HOST)   
        
        available_host_list = []
        for host in host_list:
            if host.enable and not host.exceed_vm_limit() and not host.exceed_mem_limit(mem):
                available_host_list.append(host)

        if not available_host_list:
            raise Error(ERR_HOST_FILTER_NONE)
        
        if  settings.DEBUG: print('[create_vm]', '可用主机列表', available_host_list)

        if vlan_id:
            vlan_list = [self.network_api.get_vlan_by_id(vlan_id)]
        elif net_type_id:
            vlan_list = self.network_api.get_vlan_list_by_type_id(net_type_id)
        else:
            raise Error(ERR_VM_CREATE_ARGS_VLAN)

        available_vlan_list = []
        for vlan in vlan_list:
            if vlan.enable and vlan.has_free_ip():
                available_vlan_list.append(vlan)

        if not available_vlan_list:
            raise Error(ERR_VLAN_FILTER_NONE)

        if settings.DEBUG: print('[create_vm]', '网段列表', vlan_list)

        while available_host_list:
            mac_claimed = False
            disk_created = False
            vm_db = None
        
            host = self.host_api.host_filter(available_host_list, vcpu, mem, claim=True)  
            if not host:
                raise Error(ERR_VM_HOST_FILTER)
            available_host_list.remove(host)

            if not host.alive():
                raise Error(ERR_HOST_CONNECTION)

            host_available_vlan_id_list = self.host_api.get_vlan_id_list_of_host(host.id)
            if not host_available_vlan_id_list:
                raise Error(ERR_VLAN_FILTER_NONE)

            for vlan in available_vlan_list:
                try:
                    if not vlan.id in host_available_vlan_id_list:
                        continue
                    if settings.DEBUG: print('[create_vm]', '开始创建', host, vlan)
                    mac_claimed = False
                    disk_created = False

                    mac = self.network_api.mac_claim(vlan.id, vm_uuid, ipv4=ipv4)
                    if mac:
                        mac_claimed = True
                    
                    if mac_claimed:
                        if self.image_api.init_disk(image_id, diskname):
                            disk_created = True
                        else:
                            raise Error(ERR_VM_CREATE_DISK)
                        # image_info = self.image_api.get_image_info_by_id(image_id)

                        xml_tpl = self.image_api.get_xml_tpl(image_id)
                        print(xml_tpl)
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
                            'ceph_hosts_xml': image_info['ceph_hosts_xml'],
                            'mac': mac,
                            'bridge': vlan.br
                        }
                        print(xml_desc)
                        net_info = self.network_api.get_net_info_by_vmuuid(vm_uuid)

                        vm_db = self.manager.create_vm_db({
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
                        
                        if vm_db:
                            dom = self.manager.define(host.ipv4, xml_desc)                    
                            return VM(vm_db)
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
                    if vm_db:
                        host_released = self.host_api.host_release(host, vcpu, mem)
                        if settings.DEBUG: print('[create_vm]', '释放宿主机资源', host_released)
                        vm_db_deleted = vm_db.delete()
                        if settings.DEBUG: print('[create_vm]', '删除数据库记录', vm_db_deleted)
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
                    if vm_db:
                        host_released = self.host_api.host_release(host, vcpu, mem)
                        if settings.DEBUG: print('[create_vm]', '释放宿主机资源', host_released)
                        vm_db_deleted = vm_db.delete()
                        if settings.DEBUG: print('[create_vm]', '删除数据库记录', vm_db_deleted)
                    if settings.DEBUG: print(e)
                    
        return False
    
    def delete_vm(self, vm_uuid, force=False):
        vm = self.manager.get_vm_by_uuid(vm_uuid)
        image_id = vm.image_id
        diskname = vm.disk
        host_id = vm.host_id
        vcpu = vm.vcpu
        mem = vm.mem
        mac = vm.mac
        ceph_pool_id = vm.ceph_id

        from device.api import GPUAPI
        from volume.api import VolumeAPI
        archive_disk_name = ''
        try:
            gpuapi = GPUAPI()
            if len(gpuapi.get_gpu_list_by_vm_uuid(vm_uuid)) > 0:
                raise Error(ERR_VM_DEL_GPU_MOUNTED)

            volumeapi = VolumeAPI()
            if len(volumeapi.get_volume_list_by_vm_uuid(vm_uuid)) > 0:
                raise Error(ERR_VM_DEL_VOL_MOUNTED)

            deletion_permitted = False

            if self.image_api.disk_exists(image_id, diskname,cephpool_id=ceph_pool_id):
                archive_disk_name = self.image_api.archive_disk(image_id, diskname,cephpool_id=ceph_pool_id)
                if archive_disk_name != False:
                    deletion_permitted = True
            else:
                deletion_permitted = True
        except Exception as e:
            if not force:  # 不强制删除的话抛出异常
                raise e
            else:  # 强制删除，不管其他操作是否成功，都删除虚拟机记录
                deletion_permitted = True

        if deletion_permitted:
            if vm.delete(archive_disk_name, force=force):
                if not self.host_api.host_release(host_id, vcpu, mem):
                    print('[delete_vm]', '释放宿主机资源失败')
                if not self.network_api.mac_release(mac, vm_uuid):
                    print('[delete_vm]', '释放IP地址失败')
                return True
        return False

    # def reset_vm(self, vm_uuid):
    #     vm = self.manager.get_vm_by_uuid(vm_uuid)
    #     if vm.is_running():
    #         raise Error(ERR_VM_RESET_LIVING)
    #     archive_disk_name = self.image_api.archive_disk(vm.image_id, vm.disk)
    #     if archive_disk_name != False:
    #         init_disk_success = self.image_api.init_disk(vm.image_id, vm.disk)
    #         if init_disk_success:
    #             if vm.start():
    #                 return True
    #             self.image_api.rm_disk(vm.image_id, vm.disk)
    #         self.image_api.restore_disk(vm.image_id, archive_disk_name)
    #     return False 

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
        src_host_alive = vm.is_host_connected

        from device.api import GPUAPI
        from volume.api import VolumeAPI
        gpuapi = GPUAPI()
        volumeapi = VolumeAPI()
        gpu_list = gpuapi.get_gpu_list_by_vm_uuid(vm_uuid)
        volume_list = volumeapi.get_volume_list_by_vm_uuid(vm_uuid)

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
                            'ceph_hosts_xml': image_info['ceph_hosts_xml'],
                            'mac': vm.mac,
                            'bridge': vm.br
                        }

        migrate_res = False
        if self.host_api.host_claim(host_id, vm.vcpu, vm.mem, 1):
            try:
                if src_host_alive:
                    for gpu1 in gpu_list:
                        r1 = vm.detach_device(gpu1.xml_desc)
                        if settings.DEBUG: print('[migrate_vm]', 'detach gpu ', gpu1.id, r1)
                    for volume1 in volume_list:
                        r1 = vm.detach_device(volume1.xml_desc)
                        if settings.DEBUG: print('[migrate_vm]', 'detach volume ', volume1.id, r1)

                old_host_id = vm.host_id                
                if self.manager.migrate(vm_uuid, host_id, host.ipv4, xml_desc,old_host_alive=src_host_alive):
                    migrate_res = True
                    old_res = self.host_api.host_release(old_host_id, vm.vcpu, vm.mem, 1)
                    if settings.DEBUG: print('[migrate_vm]', '释放原宿主机资源 ', old_res)
                    #重新attach device(只有云硬盘)
                    for volume1 in volume_list:
                        r1 = vm.attach_device(volume1.xml_desc)
                        if settings.DEBUG: print('[migrate_vm]', 'attach volume ', volume1.id, r1)
            except Exception as e:
                if type(e) == Error:
                    raise e
            finally:
                if not migrate_res:
                    new_res = self.host_api.host_release(host_id, vm.vcpu, vm.mem, 1)
                    if settings.DEBUG: print('[migrate_vm]', '迁移失败,释放新宿主机资源 ', new_res)


        return migrate_res

    def reset_vm(self,vm_uuid,new_image_id=None):
        vm = self.manager.get_vm_by_uuid(vm_uuid)
        if new_image_id == None:
            new_image_id = vm.image_id
        host = vm.host
        old_image_id = vm.image_id
        old_diskname = vm.disk
        old_ceph_pool_id = vm.ceph_id

        if vm.is_running():
            raise Error(ERR_VM_RESET_LIVING)

        new_image_info = self.image_api.get_image_info_by_id(new_image_id)
        if not new_image_info:
            raise Error(ERR_IMAGE_INFO)

        from device.api import GPUAPI
        from volume.api import VolumeAPI
        gpuapi = GPUAPI()
        volumeapi = VolumeAPI()        
        gpu_list = gpuapi.get_gpu_list_by_vm_uuid(vm_uuid)
        volume_list = volumeapi.get_volume_list_by_vm_uuid(vm_uuid)

        archive_disk_name = ''
        old_image_dict={ 'image_id': old_image_id,
                      'image_snap': vm.image_snap,
                      'image_name': vm.image,
                      'ceph_id': vm.ceph_id,
                      'ceph_host': vm.ceph_host,
                      'ceph_pool': vm.ceph_pool,
                      'ceph_uuid': vm.ceph_uuid,
                      'ceph_port': vm.ceph_port,
                      'ceph_username': vm.ceph_username }
        old_xml_desc = vm.xml_desc

        res = False
        try:
            #先detach设备（gpu,volume）
            for gpu1 in gpu_list:
                r1 = vm.detach_device(gpu1.xml_desc)
                if settings.DEBUG: print('[reset_vm]', 'detach gpu ', gpu1.id, r1)
            for volume1 in volume_list:
                r1 = vm.detach_device(volume1.xml_desc)
                if settings.DEBUG: print('[reset_vm]', 'detach volume ', volume1.id, r1)

            #dom的destroy和undefine操作
            dom_undefine_res = False
            if self.manager.domain_exists(vm.host_ipv4, vm.uuid):
                dom = self.manager.get_domain(vm.host_ipv4, vm.uuid)
                try:
                    dom.destroy()
                except:
                    pass
                dom.undefine()
            if not self.manager.domain_exists(vm.host_ipv4, vm.uuid):
                dom_undefine_res = True
            if dom_undefine_res:
                archive_disk_name = self.image_api.archive_disk(old_image_id, vm.disk)

            if archive_disk_name :
                init_disk_success = False
                if dom_undefine_res:
                    init_disk_success = self.image_api.init_disk(new_image_id, vm.disk)
                if init_disk_success:
                    #更新vm_db相关image信息
                    vm.db_obj.image_id = new_image_id
                    vm.db_obj.image_snap = new_image_info['image_snap']
                    vm.db_obj.image = new_image_info['image_name']
                    vm.db_obj.ceph_id = new_image_info['ceph_id']
                    vm.db_obj.ceph_host = new_image_info['ceph_host']
                    vm.db_obj.ceph_pool = new_image_info['ceph_pool']
                    vm.db_obj.ceph_uuid = new_image_info['ceph_uuid']
                    vm.db_obj.ceph_port = new_image_info['ceph_port']
                    vm.db_obj.ceph_username = new_image_info['ceph_username']
                    
                    vm.db_obj.save()

                    xml_tpl = self.image_api.get_xml_tpl(new_image_id)
                    xml_desc = xml_tpl % {
                            'name': vm.uuid,
                            'uuid': vm.uuid,
                            'mem':  vm.mem,
                            'vcpu': vm.vcpu,
                            'ceph_uuid': new_image_info['ceph_uuid'],
                            'ceph_pool': new_image_info['ceph_pool'],
                            'diskname': vm.disk,
                            'ceph_host': new_image_info['ceph_host'],
                            'ceph_port': new_image_info['ceph_port'],
                            'ceph_username': new_image_info['ceph_username'],
                            'ceph_hosts_xml': new_image_info['ceph_hosts_xml'],
                            'mac': vm.mac,
                            'bridge': vm.br
                        }
                    dom = self.manager.define(host.ipv4, xml_desc)                    
                    res = True
        except Exception as e:
            if settings.DEBUG: print('[reset_vm]', '重置镜像失败', e)
            res = False
            if archive_disk_name: #已经归档成功，重新恢复
                self.image_api.restore_disk(vm.image_id, archive_disk_name)
                
                vm.db_obj.image_id = old_image_dict['image_id']
                vm.db_obj.image_snap = old_image_dict['image_snap']
                vm.db_obj.image = old_image_dict['image_name']
                vm.db_obj.ceph_id = old_image_dict['ceph_id']
                vm.db_obj.ceph_host = old_image_dict['ceph_host']
                vm.db_obj.ceph_pool = old_image_dict['ceph_pool']
                vm.db_obj.ceph_uuid = old_image_dict['ceph_uuid']
                vm.db_obj.ceph_port = old_image_dict['ceph_port']
                vm.db_obj.ceph_username = old_image_dict['ceph_username']
                vm.db_obj.save()

                dom = self.manager.define(host.ipv4, old_xml_desc)
            if settings.DEBUG: print('[reset_vm]', '回滚成功')
        finally:
            for gpu1 in gpu_list:
                r1 = vm.attach_device(gpu1.xml_desc)
                if settings.DEBUG: print('[reset_vm]', 'attach gpu ', gpu1.id, r1)                
            for volume1 in volume_list:
                r1 = vm.attach_device(volume1.xml_desc)
                if settings.DEBUG: print('[reset_vm]', 'attach volume ', volume1.id, r1)

        return res


    def get_vm_disk_snap_list(self,vm_uuid):
        vm = self.manager.get_vm_by_uuid(vm_uuid)
        return self.image_api.get_disk_snap_list_by_disk(vm.disk)

    def create_vm_disk_snap(self,vm_uuid,remarks=None):
        vm = self.manager.get_vm_by_uuid(vm_uuid)
        res = self.image_api.create_disk_snap(vm.ceph_id,vm.disk,vm.image_id,vm_uuid,remarks=remarks)
        if res:
            return True
        else:
            return False

    def rollback_vm_disk_snap(self,vm_uuid,snap_id):
        vm = self.manager.get_vm_by_uuid(vm_uuid)
        if vm.is_running():
            if settings.DEBUG: print('[rollback_vm_disk_snap]', '运行状态无法回滚') 
            raise Error(ERR_VM_CREATE_SNAP_LIVING)
        if settings.DEBUG: print('[rollback_vm_disk_snap]', '快照回滚：开始执行') 
        res = self.image_api.rollback_disk_snap(vm.disk,snap_id)
        if settings.DEBUG: print('[rollback_vm_disk_snap]', '快照回滚：结束',res)         
        if res:
            return True
        else:
            return False

    def delete_vm_disk_snap(self,vm_uuid,snap_id):
        vm = self.manager.get_vm_by_uuid(vm_uuid)
        res = self.image_api.delete_disk_snap_by_id(vm.disk,snap_id)
        if settings.DEBUG: print('[delete_vm_disk_snap]', '快照删除',res)         
        if res:
            return True
        else:
            return False

    def set_vm_disk_snap_remarks(self,vm_uuid,snap_id,remarks=None):
        vm = self.manager.get_vm_by_uuid(vm_uuid)
        res = self.image_api.set_disk_snap_remarks(vm.disk,snap_id,remarks)       
        if res:
            return True
        else:
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
        return self.manager.get_host_by_id(host_id)

    def get_host_by_ipv4(self, host_ipv4):
        return self.manager.get_host_by_ipv4(host_ipv4)

    def get_pci_device_list_from_host(self, host_ip):
        host = self.manager.get_host_by_ipv4(host_ip)
        return host.get_pci_device_list()

    def get_vlan_id_list_of_host(self, host_id):
        return self.manager.get_vlan_id_list_of_host(host_id)

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
        return self.manager.get_host_list_by_group_id(group_id)

    def host_power_off_by_ipmi(self,host_id):
        '''通过ipmi将宿主机断电'''
        host = self.manager.get_host_by_id(host_id)
        return host.power_off_by_ipmi()

    def disable_host(self,host_id):
        '''将宿主机设置为不可用'''
        host = self.manager.get_host_by_id(host_id)
        return host.set_enable(enable=False)
    
