#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2015-10-16
#@desc:    虚拟机相关的API函数，每一个函数封装并实现一个API接口的功能。
########################################################################

from compute.group import get_group
from .tools import args_required, catch_error,print_process_time, api_log

from .error import (ERR_AUTH_PERM, ERR_VM_UUID, ERR_VM_DEFINE, ERR_VM_OP, ERR_GROUP_ID,
                    ERR_VM_NO_OP, ERR_ARGS_VM_VCPU, ERR_ARGS_VM_MEM,ERR_ARGS_VM_EDIT_NONE,
                    ERR_VM_EDIT_REMARKS, ERR_VM_EDIT, ERR_VM_MIGRATE, 
                    ERR_ARGS_VM_CREATE_NO_VLANTYPE, ERR_VM_EDIT_LIVING)
from .error import Error
from compute.vm import VM, create_vm, get_vm, migrate_vm, get_vms
from compute.host import get_host

@api_log
@catch_error
@args_required('uuid')
def get(args):
    '''获取虚拟机详细信息'''
    vm = get_vm(args['uuid'])
    if not vm:
        return {'res': False, 'err': ERR_VM_UUID}
    
    if not vm.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
    
    try:
        create_time = vm.create_time.strftime('%Y-%m-%d %H:%M:%S')
    except:
        create_time = ''
        
    info = {
        'uuid':     vm.uuid,
        'name':     vm.name, 
        'vcpu':     vm.vcpu ,
        'mem':      vm.mem ,
        'creator':       vm.creator, 
        'create_time':   create_time,
        'remarks':       vm.remarks,
        'deleted':       vm.deleted,
        'image_id':      vm.image_id,
        'image_snap':    vm.image_snap,
        'image':         vm.image,
        'host_id':       vm.host_id,
        'host_ipv4':     vm.host_ipv4,
        'group_id':      vm.group_id,
        'group_name':    vm.group_name,
        'center_id':     vm.center_id,
        'center_name':   vm.center_name, 
    
        'vlan_id':       vm.vlan_id,
        'vlan_name':     vm.vlan_name,
        'mac':           vm.mac,
        'ipv4':          vm.ipv4,
        
        'ceph_id':       vm.ceph_id,
        'ceph_host':       vm.ceph_host,
        'ceph_pool':       vm.ceph_pool
    }
    return {'res': True, 'info': info}    


@api_log
@catch_error
@args_required('group_id')
def get_list(args):
    '''获取虚拟机列表'''
    ret_list = []
    group = get_group(args['group_id'])
    if not group:
        return {'res': False, 'err': ERR_GROUP_ID}

    if not group.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
    vm_list = get_vms(args['group_id'], order = '-create_time')
    for vm in vm_list:
        if vm.create_time:
            create_time = vm.create_time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            create_time = ''
        ret_list.append({
            'uuid':         vm.uuid,
            'name':         vm.name,
            'center_id':    vm.center_id,
            'center_name':  vm.center_name,
            'group_id':     vm.group_id,
            'group_name':   vm.group_name,
            'host_id':      vm.host_id,
            'host_ipv4':    vm.host_ipv4,
            'image_id':     vm.image_id,
            'image':        vm.image,
            'ipv4':         vm.ipv4,
            'vcpu':         vm.vcpu,
            'mem':          vm.mem,
            'creator':      vm.creator,
            'create_time':  create_time,
            'remarks':      vm.remarks
            })
    return {'res': True, 'list': ret_list}
    
@api_log
@catch_error
@args_required(['group_id', 'image_id', 'vcpu', 'mem'])
def create(args):
    '''创建虚拟机'''
    if not args.has_key('net_type_id') and not args.has_key('vlan_id'):
        return {'res': False, 'err': ERR_ARGS_VM_CREATE_NO_VLANTYPE}
    
    kwargs = {}
    
    if args.has_key('net_type_id'):
        kwargs['net_type_id'] = args['net_type_id']
    
    if args.has_key('vlan_id'):
        kwargs['vlan_id'] = args['vlan_id']
    
    if args.has_key('diskname'):
        kwargs['diskname'] = args['diskname']
        
    if args.has_key('remarks'):
        kwargs['remarks'] = args['remarks']
    
    vm = create_vm(args['req_user'].username, args['group_id'], args['image_id'], args['vcpu'], args['mem'],**kwargs)
    if vm == False:
        return {'res': False, 'err': ERR_VM_DEFINE}
    
    vm.start()
    uuid = vm.uuid
    return {'res':True,'uuid':uuid}

@api_log
@catch_error
@args_required('uuid')
def status(args):
    '''获取虚拟机状态'''
    vm = get_vm(args['uuid'])
    if not vm:
        return {'res': False, 'err': ERR_VM_UUID}
    if not vm.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
    
    return {'res': True, 'status':vm.status}
    
@api_log
@catch_error
@args_required(['uuid', 'op'])
def op(args):
    '''虚拟机操作'''
    vm = get_vm(args['uuid'])
    if not vm:
        return {'res': False, 'err': ERR_VM_UUID}
    if not vm.can_operate_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
    
    #虚拟机操作类型。 key,操作代码； value,VM对象中对应处理函数名称
    op_list = {
        'start': 'start', 
        'reboot': 'reboot', 
        'shutdown': 'shutdown', 
        'poweroff': 'poweroff', 
        'delete': 'delete',
        'reset': 'reset'}
    
    if op_list.has_key(args['op']):
        try:
            res = getattr(vm, op_list[args['op']]).__call__()
        except Error, e:
            return {'res': False, 'err': e.err}
        except Exception, e:
            return {'res': False, 'err': ERR_VM_OP}
    else:
        return {'res': False, 'err': ERR_VM_NO_OP}
    if res:
        return {'res':res}
    return {'res': res, 'err': ERR_VM_OP}
    
@api_log
@catch_error
@args_required(['uuid'])
def edit(args):
    '''虚拟机参数修改'''
    vm = get_vm(args['uuid'])
    if not vm:
        return {'res': False, 'err': ERR_VM_UUID}
    if not vm.can_operate_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
    

    #参数校验
    vcpu = False
    mem  = False
    remarks = False
    if args.has_key('vcpu'):
        vcpu = args['vcpu']
        try:
            vcpu = int(vcpu)
        except:
            return {'res': False, 'err': ERR_ARGS_VM_VCPU}
        
    if args.has_key('mem'):
        mem = args['mem']
        try:
            mem = int(mem)
        except:
            return {'res': False, 'err': ERR_ARGS_VM_MEM}
    
    if args.has_key('remarks'):
        remarks = args['remarks']

    if vcpu == False and mem == False and remarks == False:
        return {'res': False, 'err': ERR_ARGS_VM_EDIT_NONE}
    
    if remarks != False:
        res = vm.set_remarks(remarks)
        if not res:
            return {'res': False, 'err': ERR_VM_EDIT_REMARKS}

    if vcpu or mem: 
        if vm.status == VM.VIR_DOMAIN_RUNNING:
            return {'res': False, 'err': ERR_VM_EDIT_LIVING}
        if vcpu:
            can_set, err = vm.can_set_vcpu(vcpu)
            if not can_set:
                return {'res': False, 'err': ERR_VM_EDIT}
        if mem:
            can_set, err = vm.can_set_mem(mem)
            if not can_set:
                return {'res': False, 'err': ERR_VM_EDIT}
            
        if vcpu:
            res = vm.set_vcpu(vcpu)
            if res and mem:
                res = vm.set_mem(mem)
                if not res:
                    vm.unset_vcpu(vcpu)
        else:
            res = vm.set_mem(mem)
    if res:
        return {'res': True}
    else:
        return {'res': False, 'err': ERR_VM_EDIT}
    
@api_log
@catch_error
@args_required(['uuid', 'host_id'])
def migrate(args):
    #被迁移虚拟机校验
    vm = get_vm(args['uuid'])
    if not vm:
        return {'res': False, 'err': ERR_VM_UUID}
    if not vm.can_operate_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
    
    #目标主机校验
    host = get_host(args['host_id'])
    if not host.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
    
    #被迁移虚拟机与目标主机是否处于同一个分中心
    if not vm.center_id == host.center_id:
        return {'res': False, 'err': ERR_AUTH_PERM}
    
    if vm.host_id == host.id:
        return {'res': False, 'err': ERR_VM_MIGRATE}
    
    res = migrate_vm(args['uuid'], args['host_id'])
    if res:
        return {'res': True}
    return {'res': False, 'err': ERR_VM_MIGRATE}

    