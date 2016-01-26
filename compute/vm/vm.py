#coding=utf-8
import libvirt

from django.conf import settings

from image import archive_disk, init_disk, get_image
from image.vmxml import DomainXML, XMLEditor
from network import get_net_info_by_vm, mac_release
from storage.ceph import get_cephpool

from ..host import host_alive, host_claim, host_release, get_host
from ..models import VM_NAME_LEN_LIMIT
from ..models import Vm, VmArchive

from api.error import Error, ERR_HOST_CONNECTION, ERR_VM_MISSING, ERR_VM_RESET_LIVING

VIR_DOMAIN_NOSTATE  =   0   #no state
VIR_DOMAIN_RUNNING  =   1   #the domain is running
VIR_DOMAIN_BLOCKED  =   2   #the domain is blocked on resource
VIR_DOMAIN_PAUSED   =   3   #the domain is paused by user
VIR_DOMAIN_SHUTDOWN =   4   #the domain is being shut down
VIR_DOMAIN_SHUTOFF  =   5   #the domain is shut off
VIR_DOMAIN_CRASHED  =   6   #the domain is crashed
VIR_DOMAIN_PMSUSPENDED =7   #the domain is suspended by guest power management
VIR_DOMAIN_LAST     =   8   #NB: this enum value will increase over time as new events are added to the libvirt API. It reflects the last state supported by this version of the libvirt API.
VIR_DOMAIN_HOST_DOWN=   9   #host down
VIR_DOMAIN_MISS     =   10  #vm miss

VM_STATE = {
    VIR_DOMAIN_NOSTATE:  'no state',
    VIR_DOMAIN_RUNNING: 'running',
    VIR_DOMAIN_BLOCKED: 'blocked',
    VIR_DOMAIN_PAUSED: 'paused',
    VIR_DOMAIN_SHUTDOWN: 'shut down',
    VIR_DOMAIN_SHUTOFF: 'shut off',
    VIR_DOMAIN_CRASHED: 'crashed',
    VIR_DOMAIN_PMSUSPENDED: 'suspended',
    VIR_DOMAIN_LAST: '',
    VIR_DOMAIN_HOST_DOWN: 'host down',
    VIR_DOMAIN_MISS: 'miss',
}

class VMData(object):
    def __init__(self, obj):
        if type(obj) == Vm:
            self.db_obj = obj
        else:
            raise RuntimeError('vm init error.')
        
                    
    def __getattr__(self, name):
        return getattr(self.db_obj, name)
    
    @property
    def group_id(self):
        if not self._group_id:
            self._group_id = self.db_obj.host.group_id
        return self._group_id
    _group_id = None
    
    @property
    def group_name(self):
        if not self._group_name:
            self._group_name = self.db_obj.host.group.name
        return self._group_name
    _group_name = None
    
    @property
    def center_id(self):
        if not self._center_id:
            self._center_id = self.db_obj.host.group.center_id
        return self._center_id
    _center_id = None
    
    @property
    def center_name(self):
        if not self._center_name:
            self._center_name = self.db_obj.host.group.center.name
        return self._center_name
    _center_name =  None
    
    @property
    def host_ipv4(self):
        if not self._host_ipv4:
            self._host_ipv4 = self.db_obj.host.ipv4
        return self._host_ipv4
    _host_ipv4 = None
    
    @property
    def vlan_id(self):
        if not self._vlan_id:
            self._get_net_info()
        return self._vlan_id
    _vlan_id = None
        
    @property
    def ipv4(self):
        if not self._ipv4:
            self._get_net_info()
        return self._ipv4
    _ipv4 = None
    
    @property
    def vlan_name(self):
        if not self._vlan_name:
            self._get_net_info()
        return self._vlan_name
    _vlan_name = None
    
    @property
    def mac(self):
        if not self._mac:
            self._get_net_info()
        return self._mac
    _mac = None
    
    @property
    def br(self):
        if not self._br:
            self._get_net_info()
        return self._br
    _br = None
    
    @property
    def ceph_id(self):
        if not self._ceph_id:
            self._get_ceph_info()
        return self._ceph_id 
    _ceph_id = None
    
    @property
    def ceph_host(self):
        if not self._ceph_host:
            self._get_ceph_info()
        return self._ceph_host
    _ceph_host = None
    
    @property
    def ceph_pool(self):
        if not self._ceph_pool:
            self._get_ceph_info()
        return self._ceph_pool
    _ceph_pool = None
    
    def _get_net_info(self):
        net_info = get_net_info_by_vm(self.db_obj.uuid)
        if not net_info:
            return False
        self._ipv4 = net_info['ipv4']
        self._vlan_id = net_info['vlan_id']
        self._vlan_name = net_info['vlan_name']
        self._mac = net_info['mac']
        self._br = net_info['br']
    
    def _get_ceph_info(self):
        image = get_image(self.db_obj.image_id)
        if not image:
            return False
        ceph_info = get_cephpool(image.cephpool_id)
        if not ceph_info:
            return False
        self._ceph_id = ceph_info.id
        self._ceph_host = ceph_info.host
        self._ceph_pool = ceph_info.pool
        
        
    def managed_by(self, user):
        if user.is_superuser:
            return True
        return user in self.db_obj.host.group.admin_user.all()
    
    def can_operate_by(self, user):
        if user.is_superuser:
            return True
        return user.username == self.db_obj.creator
    
    def set_creator(self, username):
        try:
            self.db_obj.creator = username
            self.db_obj.save()
        except:
            return False
        return True
    
    def set_remarks(self, remarks):
        try:
            self.db_obj.remarks = remarks
            self.db_obj.save()
        except:
            return False
        return True
    
    def set_host(self, host):
        host = get_host(host)
        if not host:
            return False
        self.db_obj.host_id = host.id 
        self.db_obj.save()
        return True
    
class VM(VMData):
    VIR_DOMAIN_NOSTATE  =   0   #no state
    VIR_DOMAIN_RUNNING  =   1   #the domain is running
    VIR_DOMAIN_BLOCKED  =   2   #the domain is blocked on resource
    VIR_DOMAIN_PAUSED   =   3   #the domain is paused by user
    VIR_DOMAIN_SHUTDOWN =   4   #the domain is being shut down
    VIR_DOMAIN_SHUTOFF  =   5   #the domain is shut off
    VIR_DOMAIN_CRASHED  =   6   #the domain is crashed
    VIR_DOMAIN_PMSUSPENDED =7   #the domain is suspended by guest power management
    VIR_DOMAIN_LAST     =   8   #NB: this enum value will increase over time as new events are added to the libvirt API. It reflects the last state supported by this version of the libvirt API.
    VIR_DOMAIN_HOST_DOWN=   9   #host down
    VIR_DOMAIN_MISS     =   10  #vm miss
    
    VM_STATE = {
        VIR_DOMAIN_NOSTATE:  'no state',
        VIR_DOMAIN_RUNNING: 'running',
        VIR_DOMAIN_BLOCKED: 'blocked',
        VIR_DOMAIN_PAUSED: 'paused',
        VIR_DOMAIN_SHUTDOWN: 'shut down',
        VIR_DOMAIN_SHUTOFF: 'shut off',
        VIR_DOMAIN_CRASHED: 'crashed',
        VIR_DOMAIN_PMSUSPENDED: 'suspended',
        VIR_DOMAIN_LAST: '',
        VIR_DOMAIN_HOST_DOWN: 'host down',
        VIR_DOMAIN_MISS: 'miss',
    }

    def __init__(self, obj):
        self._conn = None
        self._vm= None
        self.host_alive = False
        
        if type(obj) == Vm:
            self.db_obj = obj
#             if self.hostmanager.host_alive(self.db_obj.host.ipv4):
        else:
            raise RuntimeError('vm init error.')

    @property
    def _domain(self):
        if not self._vm:
            self._connect()
        return self._vm

    @property
    def _connection(self):
        if not self._conn:
            self._connect()
        return self._conn

    def _connect(self):
        self._conn = None
        self._vm = None
        if host_alive(self.db_obj.host.ipv4):
            self.host_alive = True
            try:
                self._conn = libvirt.open("qemu+ssh://%s/system" % self.db_obj.host.ipv4) 
            except: 
                raise Error(ERR_HOST_CONNECTION)
            else:
                try:
                    for d in self._conn.listAllDomains():
                        if d.UUIDString() == self.db_obj.uuid:
                            self._vm = d
                            return True
                except Exception as e:
                    self.error = e
                else:
                    if not self._vm:
                        self.error = 'domain not find.'
            raise Error(ERR_VM_MISSING)
        raise Error(ERR_HOST_CONNECTION)

    def start(self):
        res = self._domain.create()
        if res == 0:
            return True
        return False
    
    def reboot(self):
        res = self._domain.reboot()
        if res == 0:
            return True
        return False
    
    def shutdown(self):
        res = self._domain.shutdown()
        if res == 0:
            return True
        return False
    
    def poweroff(self):
        res = self._domain.destroy()
        if res == 0:
            return True
        return False
    
        
    def delete(self):
        
        if self.exists():
            try:
                self._domain.destroy()
            except:
                pass
            self._domain.undefine()
            
            if not self.exists():
                res = True
            else:
                res = False
        else:
            res = True

        if res and not self.exists():
            if not self.ceph_id:
                if settings.DEBUG: print('[compute.vm.vm.delete]', '获取ceph信息失败')
                return False 
            archive_success, archive_disk_name = archive_disk(self.ceph_id,  self.db_obj.disk)
            if not archive_success:
                if settings.DEBUG: print('[compute.vm.vm.delete]','archive操作失败')
                res = False
            if res:
                try:
                    archive = VmArchive()
                    archive.center_id  = self.db_obj.host.group.center.pk
                    archive.center_name= self.db_obj.host.group.center.name
                    archive.group_id   = self.db_obj.host.group.pk
                    archive.group_name = self.db_obj.host.group.name
                    archive.host_id    = self.db_obj.host.pk
                    archive.host_ipv4  = self.db_obj.host.ipv4
                    archive.ceph_host  = self.ceph_host
                    archive.ceph_pool  = self.ceph_pool
                    archive.image_id   = self.db_obj.image_id
                    archive.image_snap = self.db_obj.image_snap
                    archive.name   = self.db_obj.name
                    archive.uuid   = self.db_obj.uuid
                    archive.vcpu   = self.db_obj.vcpu
                    archive.mem    = self.db_obj.mem
                    archive.disk   = archive_disk_name
                    archive.mac    = self.mac
                    archive.ipv4   = self.ipv4
                    archive.vlan   = self.vlan_name
                    archive.br     = self.br
                    archive.remarks= self.db_obj.remarks
                    archive.creator = self.db_obj.creator
                    archive.create_time = self.db_obj.create_time
                    archive.save()
                except Exception as e:
                    if settings.DEBUG: print('[compute.vm.vm.delete]', '归档记录保存失败', e)
                    if archive_success and archive_disk_name:
                        if settings.DEBUG: print('[compute.vm.vm.delete]', '恢复虚拟机镜像')
                        revert_success, revert = archive_disk(self.ceph_id, archive_disk_name, self.db_obj.disk)
                        if not revert_success:
                            raise RuntimeError('vm archive error! revert error!!')
                    self.error = e.message
                    return False
                else:
                    if settings.DEBUG: print('[compute.vm.vm.delete]', '归档成功')
                    mac_release(archive.mac, archive.uuid)
                    host_release(self.db_obj.host, self.db_obj.vcpu, self.db_obj.mem)
                    self.db_obj.delete()
                    return True
        return False

    
    def reset(self):
        disk_archived = False
        res = True
        if res:
            #判断虚拟机是否关机
            if settings.DEBUG: print('[compute.vm.vm.reset]', '判断虚拟机是否关机')
            if (self.status == VIR_DOMAIN_RUNNING
                or self.status == VIR_DOMAIN_BLOCKED
                or self.status == VIR_DOMAIN_PAUSED
                or self.status == VIR_DOMAIN_PMSUSPENDED):
                raise Error(ERR_VM_RESET_LIVING)
        
        if res:
            #旧镜像归档
            if self.ceph_id:
                archive_success, archive_disk_name = archive_disk(self.ceph_id, self.db_obj.disk)
                if archive_success:
                    disk_archived = True
                else: 
                    if settings.DEBUG: print('[compute.vm.vm.reset]', '旧镜像归档错误')
                    res = False
            else:
                res = False
        
        disk_inited = False
        if res:
            #新镜像初始化
            init_success, init_res = init_disk(self.db_obj.image_id, self.db_obj.disk)
            if settings.DEBUG: print('[compute.vm.vm.reset]', '磁盘初始化结果：', init_success)
            if not init_success:
                res = False
            else:
                disk_inited = True
                
        if res:
            #启动虚拟机
            if not self.start():
                res = False
        
        if not res and disk_inited:
            #新镜像删除
            del_sucess, del_res = archive_disk(self.ceph_id, self.db_obj.disk)
            if not del_sucess:
                raise RuntimeError('vm reset error: new vm cant start. revert error: new image cant remove.')
            
        if not res and disk_archived:
            revert_success, revert_res = archive_disk(self.ceph_id, archive_disk_name, self.db_obj.disk)
            if not revert_success:
                raise RuntimeError('vm reset error and revert error.')
        return res

    def exists(self):
        try:
            self._connect()
        except:
            pass
        if self._vm:
            return True
        return False

    def _get_createxml_argv(self):
        ceph = self.db_obj.get_ceph()
        argv = {}
        argv['name'] = self.db_obj.name
        argv['uuid'] = self.db_obj.uuid
        argv['memory'] = self.db_obj.mem
        argv['vcpu'] = self.db_obj.vcpu
        argv['ceph_uuid'] = ceph.uuid
        argv['ceph_pool'] = ceph.pool
        argv['diskname'] = self.db_obj.disk
        argv['ceph_host'] = ceph.host
        argv['ceph_port'] = ceph.port
        argv['mac'] = self.db_obj.mac
        argv['bridge'] = self.br
        return argv

    def can_set_vcpu(self, vcpu):
        if self.status == 1:
            return False, 'can not set vcpu when vm is running.'
        if not isinstance(vcpu, int):
            return False, 'vcpu must be a integer'
        if vcpu <= 0:
            return False, 'mem must be a positive integer'
        return True, ''
    
    def set_vcpu(self, vcpu):
        if vcpu == self.db_obj.vcpu:
            return True
        
        #记录变化
        self.vcpu_change = vcpu - self.db_obj.vcpu

        #修改XML
        xml = XMLEditor()
        xml.set_xml(self._domain.XMLDesc())
        root = xml.get_root()
        try:
            root.getElementsByTagName('vcpu')[0].firstChild.data = vcpu
        except:
            return False
        xmldesc = root.toxml()
        
        #修改Host资源信息
        if self.vcpu_change > 0:
#             res = self.hostmanager.claim(self.db_obj.host, self.vcpu_change, 0, 0)
            res = host_claim(self.db_obj.host, self.vcpu_change, 0, 0)
        else:
#             res = self.hostmanager.release(self.db_obj.host, -self.vcpu_change, 0, 0)                
            res = host_release(self.db_obj.host, -self.vcpu_change, 0, 0)
        if res == True:
            self.db_obj.vcpu += self.vcpu_change
            self.db_obj.save()
            try:
                res = self._connection.defineXML(xmldesc)
            except Exception as e:
                reset = self.unset_vcpu()
                if not reset:
                    raise RuntimeError('set vcpu error, can not reset.')
                return False
            return True
        return False
    
    def unset_vcpu(self):
        reset = False
        if self.vcpu_change > 0:
#             reset = self.hostmanager.release(self.db_obj.host, self.vcpu_change, 0, 0)
            reset = host_release(self.db_obj.host, self.vcpu_change, 0, 0)
        elif self.vcpu_change < 0:
#             reset = self.hostmanager.claim(self.db_obj.host, -self.vcpu_change, 0, 0)
            reset = host_claim(self.db_obj.host, -self.vcpu_change, 0, 0)
        if reset == True:
            self.db_obj.vcpu -= self.vcpu_change
            self.db_obj.save()
            self.vcpu_change = 0
        return reset

    def can_set_mem(self, mem):
        if self.status == 1:
            return False, 'can not set mem when vm is running.'
        if not isinstance(mem, int):
            return False, 'mem must be a integer'
        if mem <= 0:
            return False, 'mem must be a positive integer'
        return True, ''
        
    def set_mem(self, mem):
        if mem == self.db_obj.mem:
            return True
        
        #记录变化
        self.mem_change = mem - self.db_obj.mem 
        
        #修改XML
        xml = XMLEditor()
        xml.set_xml(self._domain.XMLDesc())
        node = xml.get_node([ 'memory'])
        if node:
            node.attributes['unit'].value = 'MiB'
            node.firstChild.data = mem
        node1 = xml.get_node(['currentMemory'])
        if node1:
            node1.attributes['unit'].value = 'MiB'
            node1.firstChild.data = mem
        xmldesc = xml.get_root().toxml()
        
        #修改Host资源信息
        if self.mem_change > 0:
#             res = self.hostmanager.claim(self.db_obj.host, 0, self.mem_change, 0)
            res = host_claim(self.db_obj.host, 0, self.mem_change, 0)
        else:
#             res = self.hostmanager.release(self.db_obj.host, 0, -self.mem_change, 0)
            res = host_release(self.db_obj.host, 0, -self.mem_change, 0)
                      
        if res == True:
            self.db_obj.mem += self.mem_change
            self.db_obj.save()
            try:
                res = self._connection.defineXML(xmldesc)
            except Exception as e:
                reset = self.unset_mem()
                if not reset:
                    raise RuntimeError('set mem error, can not reset.')
                return False
            return True
        return False
    
    def unset_mem(self):
        reset = False
        if self.mem_change > 0:
#             reset = self.hostmanager.release(self.db_obj.host, 0, self.mem_change, 0)
            reset = host_release(self.db_obj.host, 0, self.mem_change, 0)
        elif self.mem_change < 0:
#             reset = self.hostmanager.claim(self.db_obj.host, 0, -self.mem_change, 0)
            reset = host_claim(self.db_obj.host, 0, -self.mem_change, 0)
        if reset == True:
            self.db_obj.mem -= self.mem_change
            self.db_obj.save()
            self.mem_change = 0
        return reset
    
    @property
    def status(self):
        try:
            info = self._domain.info()
            return info[0]
        except Exception as e:
            if not self.host_alive:
                return VIR_DOMAIN_HOST_DOWN
            return VIR_DOMAIN_MISS
    
    def attach_device(self, xml):
        try:
            res = self._domain.attachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CONFIG)
        except Exception as e:
            if 'already in the domain configuration' in str(e):
                res = 0
            else:
                res = -1
        if res == 0:
            return True
        return False

    def detach_device(self, xml):
        res = self._domain.detachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CONFIG)
        if res == 0:
            return True
        return False
    