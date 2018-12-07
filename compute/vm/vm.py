#coding=utf-8
import libvirt

from django.db import transaction
from django.conf import settings

from image.vmxml import  XMLEditor

from ..models import Vm as DBVm
from ..models import VmArchive

from api.error import Error

from ..manager import VirtManager

VIR_DOMAIN_NOSTATE = 0  # no state
VIR_DOMAIN_RUNNING = 1  # the domain is running
VIR_DOMAIN_BLOCKED = 2  # the domain is blocked on resource
VIR_DOMAIN_PAUSED = 3  # the domain is paused by user
VIR_DOMAIN_SHUTDOWN = 4  # the domain is being shut down
VIR_DOMAIN_SHUTOFF = 5  # the domain is shut off
VIR_DOMAIN_CRASHED = 6  # the domain is crashed
VIR_DOMAIN_PMSUSPENDED = 7  # the domain is suspended by guest power management
VIR_DOMAIN_LAST = 8  # NB: this enum value will increase over time as new events are added to the libvirt API. It reflects the last state supported by this version of the libvirt API.
VIR_DOMAIN_HOST_DOWN = 9  # host connect failed
VIR_DOMAIN_MISS = 10  # vm miss

VM_STATE = {
    VIR_DOMAIN_NOSTATE: 'no state',
    VIR_DOMAIN_RUNNING: 'running',
    VIR_DOMAIN_BLOCKED: 'blocked',
    VIR_DOMAIN_PAUSED: 'paused',
    VIR_DOMAIN_SHUTDOWN: 'shut down',
    VIR_DOMAIN_SHUTOFF: 'shut off',
    VIR_DOMAIN_CRASHED: 'crashed',
    VIR_DOMAIN_PMSUSPENDED: 'suspended',
    VIR_DOMAIN_LAST: '',
    VIR_DOMAIN_HOST_DOWN: 'host connect failed',
    VIR_DOMAIN_MISS: 'miss',
}

class VMData(object):
    def __init__(self, obj):
        if type(obj) == DBVm:
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
    
    # @property
    # def vlan_id(self):
    #     if not self._vlan_id:
    #         self._get_net_info()
    #     return self._vlan_id
    # _vlan_id = None
        
    # @property
    # def ipv4(self):
    #     if not self._ipv4:
    #         self._get_net_info()
    #     return self._ipv4
    # _ipv4 = None
    
    # @property
    # def vlan_name(self):
    #     if not self._vlan_name:
    #         self._get_net_info()
    #     return self._vlan_name
    # _vlan_name = None
    
    # @property
    # def mac(self):
    #     if not self._mac:
    #         self._get_net_info()
    #     return self._mac
    # _mac = None
    
    # @property
    # def br(self):
    #     if not self._br:
    #         self._get_net_info()
    #     return self._br
    # _br = None
    
    # @property
    # def ceph_id(self):
    #     if not self._ceph_id:
    #         self._get_ceph_info()
    #     return self._ceph_id 
    # _ceph_id = None
    
    # @property
    # def ceph_host(self):
    #     if not self._ceph_host:
    #         self._get_ceph_info()
    #     return self._ceph_host
    # _ceph_host = None
    
    # @property
    # def ceph_pool(self):
    #     if not self._ceph_pool:
    #         self._get_ceph_info()
    #     return self._ceph_pool
    # _ceph_pool = None
    
    # def _get_net_info(self):
    #     net_info = get_net_info_by_vm(self.db_obj.uuid)
    #     if not net_info:
    #         return False
    #     self._ipv4 = net_info['ipv4']
    #     self._vlan_id = net_info['vlan_id']
    #     self._vlan_name = net_info['vlan_name']
    #     self._mac = net_info['mac']
    #     self._br = net_info['br']
    
    # def _get_ceph_info(self):
    #     image = get_image(self.db_obj.image_id)
    #     if not image:
    #         return False
    #     ceph_info = get_cephpool(image.cephpool_id)
    #     if not ceph_info:
    #         return False
    #     self._ceph_id = ceph_info.id
    #     self._ceph_host = ceph_info.host
    #     self._ceph_pool = ceph_info.pool
        
        
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
        except Exception as e:
            return False
        return True
    
    def set_host(self, host_id):
        res = True
        with transaction.atomic():
            db = DBVm.objects.select_for_update().get(pk = self.db_obj.id)
            db.host_id = host_id
            try:
                db.save()
            except:
                res = False
            else:
                self.db_obj = db
        return res

    def set_ha_monitored(self, ha_monitored):
        try:
            if ha_monitored:
                self.db_obj.ha_monitored = True
            else:
                self.db_obj.ha_monitored = False
            self.db_obj.save(update_fields=['ha_monitored'])
        except Exception as e:
            return False
        return True
    
class VM(VMData, VirtManager):
    def __init__(self, obj):
        self._conn = None
        self._vm= None
        self.old_vcpu = None
        self.old_mem = None
        
        if type(obj) == DBVm:
            self.db_obj = obj
        else:
            raise RuntimeError('vm init error.')

    @property
    def _domain(self):
        if not self._vm:
            self._connect()
        return self._vm

    @property
    def xml_desc(self):
        dom = self.get_domain(self.host_ipv4, self.uuid)
        return dom.XMLDesc()

    @property
    def is_host_connected(self):
        try:
            self._conn = self._get_connection(self.db_obj.host.ipv4)
            return True
        except Exception:
            return False

    def _connect(self):
        self._conn = self._get_connection(self.db_obj.host.ipv4)
        self._vm = self.get_domain(self.db_obj.host.ipv4, self.db_obj.uuid)

    def start(self):
        dom = self.get_domain(self.host_ipv4, self.uuid)
        res = dom.create()
        if res == 0:
            return True
        return False
    
    def reboot(self):
        dom = self.get_domain(self.host_ipv4, self.uuid)
        res = dom.reboot()
        if res == 0:
            return True
        return False
    
    def shutdown(self):
        dom = self.get_domain(self.host_ipv4, self.uuid)
        res = dom.shutdown()
        if res == 0:
            return True
        return False
    
    def poweroff(self):
        dom = self.get_domain(self.host_ipv4, self.uuid)
        res = dom.destroy()
        if res == 0:
            return True
        return False
    
        
    def delete(self, archive_disk_name=None, force=False):
        try:
            if self.domain_exists(self.host_ipv4, self.uuid):
                dom = self.get_domain(self.host_ipv4, self.uuid)
                try:
                    dom.destroy()
                except:
                    pass
                dom.undefine()
                if self.domain_exists(self.host_ipv4, self.uuid):
                    res = False
                else:
                    res = True
            else:
                res = True
        except Exception as e:
            import traceback 
            traceback.print_exc()

            if force:
                res = True 
            else:
                raise e    
                
        if force or (res and not self.domain_exists(self.host_ipv4, self.uuid)):
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
                self.error = e
                return False
            else:
                if settings.DEBUG: print('[compute.vm.vm.delete]', '归档成功')
                self.db_obj.delete()
                return True
        return False

    def exists(self):
        try:
            self._connect()
        except:
            pass
        if self._vm:
            return True
        return False

    def is_running(self):
        if (self.status == VIR_DOMAIN_RUNNING
            or self.status == VIR_DOMAIN_BLOCKED
            or self.status == VIR_DOMAIN_PAUSED
            or self.status == VIR_DOMAIN_PMSUSPENDED):
            return True
        return False

    def is_shutted_off(self):
        return self.status == VIR_DOMAIN_SHUTOFF

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

    def set_vcpu(self, vcpu):
        if self.is_running():
            return False
        if not isinstance(vcpu, int):
            return False
        if vcpu <= 0:
            return False

        res = True
        try:
            with transaction.atomic():
                db = DBVm.objects.select_for_update().get(pk = self.db_obj.id)
                old_vcpu = db.vcpu
                db.vcpu = vcpu
            
                db.save()
                self.db_obj = db
                self.old_vcpu = old_vcpu
        except:
            res = False
        return res
        
    def restore_vcpu(self):
        if not self.old_vcpu:
            return False

        res = True
        try:
            with transaction.atomic():
                db = DBVm.objects.select_for_update().get(pk = self.db_obj.id)
                db.vcpu = self.old_vcpu
                
                db.save()
                self.db_obj = db
        except:
            res = False
        return res

    def set_mem(self, mem):
        if self.is_running():
            return False
        if not isinstance(mem, int):
            return False
        if mem <= 0:
            return False

        res = True
        try:
            with transaction.atomic():
                db = DBVm.objects.select_for_update().get(pk = self.db_obj.id)
                old_mem = db.mem
                db.mem = mem
            
                db.save()
                self.db_obj = db
                self.old_mem = old_mem
        except:
            res = False
        return res

    def restore_mem(self):
        if not self.old_mem:
            return False

        res = True
        try:
            with transaction.atomic():
                db = DBVm.objects.select_for_update().get(pk = self.db_obj.id)
                db.mem = self.old_mem
            
                db.save()
                self.db_obj = db
        except:
            res = False    
        return res

    @property
    def status(self):
        try:
            info = self._domain.info()
            return info[0]
        except Exception:
            if self._conn:
                return VIR_DOMAIN_MISS
            else:
                return VIR_DOMAIN_HOST_DOWN
    
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

    def get_disk_list(self):
        # print(self._domain.XMLDesc())
        dev_list = []
        xml = XMLEditor()
        xml.set_xml(self._domain.XMLDesc())
        root = xml.get_root()
        devices = root.getElementsByTagName('devices')[0].childNodes
        for d in devices:
            if d.nodeName == 'disk':
                for disk_child in d.childNodes:
                    if disk_child.nodeName == 'target':
                        dev_list.append(disk_child.getAttribute('dev'))
        return dev_list
    
