#coding=utf-8

###############################################
# name: 虚拟机管理平台 计算模块 虚拟机管理模块
# author: bobfu
# email: fubo@cnic.cn
# time: 2015-10-10
###############################################

from ..models import Vm as ModelVm

from .manager import VMManager
from .vm import VMData, VM

vmmanager = VMManager()

def create_vm(user, group_id, image_id, vcpu, mem, net_type_id=None, vlan_id=None, 
              diskname=None, remarks=None):
    '''net_type_id 和 vlan_id 不能同时为None'''
    args = {
        'group_id': group_id,
        'image_id': image_id,
        'vcpu': vcpu,
        'mem': mem
    }
    
    if net_type_id == None:
        if vlan_id:
            vlan = get_vlan(vlan_id)
            if vlan:
                args['net_type_id'] = vlan.type_code
                args['vlan_id'] = vlan.id
            else:
                return False
        else:
            return False
    else:
        args['net_type_id'] = net_type_id

    if diskname != None:
        args['diskname'] = diskname
    if remarks != None:
        args['remarks'] = remarks
    vm = vmmanager.define(args)
    if vm != False:
        vm.set_creator(user)
    return vm
        

def migrate_vm(vm_uuid, host):
    return vmmanager.migrate(vm_uuid, host)

def get_vm(vm_uuid):
    vm = ModelVm.objects.filter(uuid = vm_uuid)
    if not vm.exists():
        return False
    return VM(vm[0])

def get_vms(group_id, host_id = None, order = None):
    if host_id == None:
        vms = ModelVm.objects.filter(host__group_id = group_id)
        print(vms, group_id)
    else:
        vms = ModelVm.objects.filter(host__group_id = group_id, host_id = host_id)
    if order:
        vms = vms.order_by(order)
    ret_list = []
    for vm in vms:
        ret_list.append(VMData(vm))
    return ret_list