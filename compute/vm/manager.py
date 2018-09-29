#coding=utf-8
import uuid
from django.conf import settings
from compute.models import MigrateLog

from image.vmxml import DomainXML

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

from ..manager import VirtManager

from ..models import Vm as DBVm
from .vm import VMData
from .vm import VM

class VMManager(VirtManager):
    def __init__(self):
        self.error = ''
        self.db_model = DBVm

    def create_vm_uuid(self):
        return str(uuid.uuid4())
    
    def create_vm_db(self, args):
        db = self.db_model()
        db.deleted=False
        for field in args:
            setattr(db, field, args[field])
        try:
            db.save()
        except Exception as e:
            print(e)
            return False
        return db
    
    def migrate(self, vm_uuid, host_id, host_ipv4, xml_desc, old_host_alive=True):
        '''迁移虚拟机'''
        vm = self.get_vm_by_uuid(vm_uuid)
        old_host_id = vm.host_id
        old_host_ipv4 = vm.host_ipv4
        old_xml_desc = vm.xml_desc        

        res = False
        error = ''
        undefined = False
        if not old_host_alive:
            if vm.set_host(host_id):
                if self.define(host_ipv4, xml_desc):
                    res = True
                else:
                    error += '创建虚拟机失败,'
                    if not vm.set_host(old_host_id):
                        error += '数据库还原失败,'
        elif self.undefine(old_host_ipv4, vm_uuid):
            undefined = True
            if vm.set_host(host_id):
                if self.define(host_ipv4, xml_desc):
                    res = True
                else:
                    error += '创建虚拟机失败,'
                    if not vm.set_host(old_host_id):
                        error += '数据库还原失败,'
                    if not self.define(old_host_ipv4, old_xml_desc):
                        error += '重建虚拟机失败,'
            else:
                error += '数据库修改失败,'
                if not self.define(old_host_ipv4, old_xml_desc):
                    error += '重建虚拟机失败,'
        else:
            error += '删除虚拟机失败,'
        
        #迁移日志
        log = MigrateLog()
        log.vmid = vm_uuid
        log.src_host_ipv4 = old_host_ipv4
        log.dst_host_ipv4 = host_ipv4   
        log.error = self.error  
        log.result = res 
        log.src_undefined = undefined
        log.save()
        return res
    
    def get_vm_list_by_group_id(self, group_id, host_id=None, order=None, ha_monitored=None):
        if host_id == None:
            vms = DBVm.objects.filter(host__group_id = group_id)
        else:
            vms = DBVm.objects.filter(host__group_id = group_id, host_id = host_id)        
        if ha_monitored == True:
            vms = vms.filter(ha_monitored=True)
        elif ha_monitored == False:
            vms = vms.filter(ha_monitored=False)            
        if order:
            vms = vms.order_by(order)
        ret_list = []
        for vm in vms:
            ret_list.append(VMData(vm))
        return ret_list

    def get_ha_monitored_vm_list(self, ha_monitored=True):
        if ha_monitored:
            vms = DBVm.objects.filter(ha_monitored = True)
        else:
            vms = DBVm.objects.filter(ha_monitored = False)        
        ret_list = []
        for vm in vms:
            ret_list.append(VMData(vm))
        return ret_list

    def get_vm_by_uuid(self, vm_uuid):
        if not vm_uuid:
            raise Error(ERR_VM_UUID)
        vm = DBVm.objects.filter(uuid = vm_uuid)
        if not vm.exists():
            raise Error(ERR_VM_UUID)
        return VM(vm[0])

    def vm_uuid_exists(self, vm_uuid):
        vm = DBVm.objects.filter(uuid = vm_uuid)
        return vm.exists()


    def set_vm_configuration(self, vm_uuid, vcpu=None, mem=None):
        vm = self.get_vm_by_uuid(vm_uuid)

        xml_desc = vm.xml_desc
        if vcpu:
            xml_desc = self._xml_edit_vcpu(xml_desc, vcpu)
        if xml_desc and mem:
            xml_desc = self._xml_edit_mem(xml_desc, mem)
        
        if xml_desc:
            res = True
            if vcpu: 
                set_vcpu_success = vm.set_vcpu(vcpu)
            else:
                set_vcpu_success = True
            if mem:
                set_mem_success = vm.set_mem(mem)
            else:
                set_mem_success = True

            if not set_vcpu_success or not set_mem_success:
                vm.restore_vcpu()
                vm.restore_mem()
            else:
                return self.define(vm.host_ipv4, xml_desc)
        return False
