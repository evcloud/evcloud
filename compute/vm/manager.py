#coding=utf-8
import libvirt
import uuid
from django.conf import settings
from compute.models import VM_NAME_LEN_LIMIT
from compute.models import Vm
from compute.models import MigrateLog
from compute.host import host_alive
from compute.host import get_available_hosts
from compute.host import host_filter 
from compute.host import host_claim
from compute.host import host_release
from compute.host import get_host

from image import init_disk
from image import get_image_info
from image.vmxml import DomainXML
from .vm import VM
from .vm import VIR_DOMAIN_RUNNING
from .vm import VIR_DOMAIN_BLOCKED
from .vm import VIR_DOMAIN_PAUSED
from .vm import VIR_DOMAIN_PMSUSPENDED

from api.error import Error
from api.error import ERR_GROUP_ID
from api.error import ERR_HOST_ID
from api.error import ERR_HOST_FILTER_NONE
from api.error import ERR_HOST_CLAIM
from api.error import ERR_HOST_CONNECTION
from api.error import ERR_VM_NAME
from api.error import ERR_VM_UUID
from api.error import ERR_VLAN_FILTER_NONE
from api.error import ERR_VLAN_TYPE_ID
from api.error import ERR_VM_MIGRATE_DIFF_CEPH
from api.error import ERR_VM_MIGRATE_LIVING

from network import vlan_type_exists
from network import vlan_exists
from network import get_vlans_by_type
from network import vlan_filter
from network import get_net_info_by_vm
from network import mac_release

from ..manager import VirtManager

class VMManager(VirtManager):
    def __init__(self):
        self.error = ''
    
    def _filter_vlan_and_host(self, group_id, vlan_type_code, vcpu, mem, vmid, vlan_id = None):
        '''根据集群id，网络类型/网络id筛选出合适的宿主机'''
        if settings.DEBUG: print('[_filter_vlan_and_host]', '主机筛选开始：', group_id, vlan_type_code, vcpu, mem, vmid, vlan_id)
        
        #参数检查
        if not vlan_id:
            if not vlan_type_exists(vlan_type_code):
                if settings.DEBUG: print('[_filter_vlan_and_host]', '参数错误')
                return False
        else:
            if not vlan_exists(vlan_id, vlan_type_code=vlan_type_code):
                if settings.DEBUG: print('[_filter_vlan_and_host]', '参数错误')
                return False
        
        #获取可用宿主机列表
#         hosts = self.hostmanager.available_hosts(group_id)
        if settings.DEBUG: print('[_filter_vlan_and_host]', '开始获取可用主机列表')
        hosts = get_available_hosts(group_id)
        if settings.DEBUG: print('[_filter_vlan_and_host]', '成功获取：', hosts)
        if hosts == []:
            return False
        
        if settings.DEBUG: print('[_filter_vlan_and_host]', '开始获取可用网络')
        if not vlan_id:
            vlan_id_list = [vlan.id for vlan in get_vlans_by_type(vlan_type_code)]
        else:
            vlan_id_list = [int(vlan_id)]
        if settings.DEBUG: print('[_filter_vlan_and_host]', '成功获取：', vlan_id_list)
        
        if settings.DEBUG: print('[_filter_vlan_and_host]', '根据网络列表剔除不可用宿主机')
        net_available_hosts = []
        for host in hosts:
            if host.vlan.filter(id__in = vlan_id_list).exists():
                net_available_hosts.append(host)
        if settings.DEBUG: print('[_filter_vlan_and_host]', '剔除成功', net_available_hosts)
        
        #筛选
        if settings.DEBUG: print('[_filter_vlan_and_host]', '开始筛选')
        best_host = False
        while net_available_hosts:
#             best_host = self.hostmanager.filter(net_available_hosts, vcpu, mem, claim=True)
            if settings.DEBUG: print('[_filter_vlan_and_host]', '主机资源池', net_available_hosts)
            best_host = host_filter(net_available_hosts, vcpu, mem, claim=True)
            if best_host:
                if settings.DEBUG:  print('[_filter_vlan_and_host]', '获取到一个宿主机', best_host)
#                 if self.hostmanager.host_alive(best_host.ipv4):
                if host_alive(best_host.ipv4):
                    if settings.DEBUG: print('[_filter_vlan_and_host]', '预筛选网络' , vlan_id_list)
                    
                    vlan_id_in_best_host = [vlan.id for vlan in best_host.vlan.filter(enable=True) ######start
                                            if vlan.id in vlan_id_list]
                    if settings.DEBUG: print('[_filter_vlan_and_host]', 'ping主机成功，开始筛选网络', vlan_id_in_best_host)
                    vlan = vlan_filter(vlan_id_in_best_host, claim=True, vmid=vmid)
                    if vlan:                           
                        if settings.DEBUG: print('[_filter_vlan_and_host]', '找到最佳主机', best_host, vlan)
                        return best_host, vlan
#                     self.hostmanager.release(best_host, vcpu, mem)
                host_release(best_host, vcpu, mem)
                net_available_hosts.remove(best_host)
                if settings.DEBUG: print('[_filter_vlan_and_host]', '该主机不可用，释放资源')
            else:
                break
        
        return False
        

    def define(self, args):
        '''定义虚拟机  args 'group_id', 'image_id', 
        'net_type_id' , 'vcpu', 'mem', ['vlan_id', 'diskname', 'remarks'] ''' 
        if settings.DEBUG: print('create vm:', args)
        try:
            host_claimed = False
            ip_claimed = False
            
            #参数补充
            if settings.DEBUG: print('参数补充')
            args['uuid'] = str(uuid.uuid4())
            args['name'] = args['uuid']
            
            #参数验证
            if settings.DEBUG: print('参数验证')
            if len(args['name']) > VM_NAME_LEN_LIMIT:
                raise Error(ERR_VM_NAME)
            args['mem'] = int(args['mem'])
            args['vcpu'] = int(args['vcpu'])
            
            if 'net_type_id' not in args:
                raise Error(ERR_VLAN_TYPE_ID)
            
            if 'group_id' not in args:
                raise Error(ERR_GROUP_ID)
            
            if 'vlan_id' in args:
                vlan_id = args['vlan_id']
            else:
                vlan_id = None
            
            #宿主机筛选
            filter_res = self._filter_vlan_and_host(args['group_id'], args['net_type_id'], 
                                                    args['vcpu'], args['mem'], args['uuid'], 
                                                    vlan_id = vlan_id)
            if not filter_res:
                raise Error(ERR_HOST_FILTER_NONE)
            
            host = filter_res[0]
            vlan = filter_res[1]
            host_claimed = True
            ip_claimed = True
            
            net_info = get_net_info_by_vm(args['uuid'])
            if not net_info:
                raise Error(ERR_VLAN_FILTER_NONE)
            mac = net_info['mac']
            ipv4 = net_info['ipv4']

            args['mac'] = mac 
            args['bridge'] = vlan.br
            
            if 'diskname' not in args:
                #根磁盘初始化
                args['diskname'] = args['uuid']
                if settings.DEBUG: print('根磁盘初始化', args['diskname'])
                init_res, tmp = init_disk(args['image_id'], args['diskname'])
                if settings.DEBUG: print('磁盘初始化结果：', init_res)
                if not init_res:
                    raise RuntimeError('disk init error. %s' % tmp)
            
#             diskinfo = self.imagemanager.get_image_info(args['image_id'])
            get_disk_info_success, disk_info = get_image_info(args['image_id'])
            
            if settings.DEBUG: print(disk_info)
            
            if not get_disk_info_success:
                raise Error(disk_info)
            args.update(disk_info)
                
#             print args
            
            if settings.DEBUG: print(args)
            
            #创建虚拟机
            if settings.DEBUG: print('创建虚拟机')
            xml = DomainXML(args['image_id'])
            xmldesc = xml.render(args)

            conn = self._connection(host.ipv4)
            vm = conn.defineXML(xmldesc)
            
            if 'remarks' in args:
                remarks = args['remarks']
            else:
                remarks = ''
            
            obj = Vm()
            obj.host_id    = host.id
            obj.image_id = args['image_id']
            obj.image_snap   = args['image_snap']
            obj.image   = args['image_name']
            obj.uuid    = str(args['uuid'])
            obj.name    = str(args['name'])
            obj.vcpu    = args['vcpu']
            obj.mem     = args['mem']
            obj.disk    = str(args['diskname'])
            obj.deleted = False
            obj.remarks = remarks
            obj.save()

        except Exception as e:
            #释放资源
            if settings.DEBUG: print(e, '释放资源', host_claimed, ip_claimed)
            if host_claimed:
                host_release(host, args['vcpu'], args['mem'])
                
            if ip_claimed:
                mac_release(mac, args['uuid'])
            
#             self.error = e.message
#             return False
            raise e
        else:
            return VM(obj)
    
    def migrate(self, vmid, host):
        '''迁移虚拟机'''
        try:
            obj = Vm.objects.get(uuid = vmid)
        except:
            if settings.DEBUG: print('[compute.vm.manager.migrate]', 'uuid error.')
            raise Error(ERR_VM_UUID)
        
        vm = VM(obj)
        old_host_id = vm.host_id
        old_host_ipv4 = vm.host_ipv4
        
#         host = self.hostmanager.check_host(host)
        host = get_host(host)
        if not host:
            if settings.DEBUG: print('[compute.vm.manager.migrate]', 'host error.')
            raise Error(ERR_HOST_ID)
        
        
        #判断是否可迁移到目标主机
        #是否属于同一个center
        
        if settings.DEBUG: print('[compute.vm.manager.migrate]', '判断是否可迁移到目标主机') 
        if vm.center_id != host.center_id:
            if settings.DEBUG: print('[compute.vm.manager.migrate]', '不可迁移') 
            raise Error(ERR_VM_MIGRATE_DIFF_CEPH)
        
        #判断虚拟机是否关机
        if settings.DEBUG: print('[compute.vm.manager.migrate]', '判断虚拟机是否关机')
        
        if (vm.status == VIR_DOMAIN_RUNNING
            or vm.status == VIR_DOMAIN_BLOCKED
            or vm.status == VIR_DOMAIN_PAUSED
            or vm.status == VIR_DOMAIN_PMSUSPENDED):
            if settings.DEBUG: print('[compute.vm.manager.migrate]', '未关机')
            raise Error(ERR_VM_MIGRATE_LIVING)
        
        #在新宿主机上创建虚拟机
        if settings.DEBUG: print('[compute.vm.manager.migrate]', '在新宿主机上创建虚拟机')
        define_args = {
            'uuid': vm.uuid,
            'name': vm.name,
            'host_id': host.id, 
            'image_id': vm.image_id,
            'mac': vm.mac,
            'bridge': vm.br, 
            'vcpu': vm.vcpu, 
            'mem': vm.mem,
            'diskname': vm.disk}
        
        get_info_success, disk_info = get_image_info(vm.db_obj.image_id)
        if get_info_success:
            define_args.update(disk_info)
        else:
            raise Error(disk_info)
        
        #申请资源
        if not host_claim(host, vm.vcpu, vm.mem):
            if settings.DEBUG: print('[compute.vm.manager.migrate]', '申请资源失败')
            raise Error(ERR_HOST_CLAIM)
    
        vm_created = False
        try:    
            #创建虚拟机
            if settings.DEBUG: print('[compute.vm.manager.migrate]', '创建虚拟机')
            xml = DomainXML(define_args['image_id'])
            xmldesc = xml.render(define_args)
            if settings.DEBUG: print('[compute.vm.manager.migrate]', 'connecte to ', host.ipv4)
            conn = self._connection(host.ipv4)
            
            if settings.DEBUG: print('[compute.vm.manager.migrate]', 'define xml')
            new_domain = conn.defineXML(xmldesc)
            
            if new_domain:
                vm_created = True
            else:
                if settings.DEBUG: print('[compute.vm.manager.migrate]', 'define error.')
                raise RuntimeError('vm define error.')
            
            #启动新虚拟机
            if settings.DEBUG: print('[compute.vm.manager.migrate]', 'create vm', new_domain)
            if new_domain.create() != 0:
                if settings.DEBUG: print('[compute.vm.manager.migrate]', 'create vm error.')
                raise RuntimeError('start vm error.')
                
            #修改数据库
            if not vm.set_host(host):
                pass
            
        except Exception as e:
            if settings.DEBUG: print('[compute.vm.manager.migrate]',  e)
            self.error = e.message 
            tmp = host_release(host, vm.vcpu, vm.mem)
            if settings.DEBUG: print('释放资源: ', host, vm.vcpu, vm.mem, tmp)
            
            if vm_created:
                try:
                    new_domain.destroy()
                except: pass
                new_domain.undefine()
            res = False
        else:
            #删除原虚拟机
            if vm._vm.undefine() == 0:
                host_release(old_host_id, vm.vcpu, vm.mem)
            else:
                self.error = '原宿主机资源未释放'
            res = True
            
        #迁移日志
        log = MigrateLog()
        log.vmid = vm.uuid
        log.src_host_ipv4 = old_host_ipv4
        log.dst_host_ipv4 = host.ipv4        
                
        if res:
            log.result = True
        else:
            log.error = self.error
            log.result = False
        log.save()
        return res
     
