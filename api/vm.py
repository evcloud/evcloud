#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2015-10-16
#@desc:    虚拟机相关的API函数，每一个函数封装并实现一个API接口的功能。
########################################################################

from .tools import args_required
from .tools import catch_error
from .tools import api_log

from .error import ERR_AUTH_PERM
from .error import ERR_VM_UUID
from .error import ERR_VM_DEFINE
from .error import ERR_VM_OP
from .error import ERR_VM_NO_OP
from .error import ERR_VM_EDIT
from .error import ERR_VM_MIGRATE
from .error import Error

from compute.api import VmAPI
from compute.api import GroupAPI
from compute.api import HostAPI

@api_log
@catch_error
@args_required('uuid')
def get(args):
    '''获取虚拟机详细信息'''
    api = VmAPI()
    vm = api.get_vm_by_uuid(args['uuid'])
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
    api = VmAPI()
    group_api = GroupAPI()
    group = group_api.get_group_by_id(args['group_id'])
    if not group.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}

    vm_list = api.get_vm_list_by_group_id(args['group_id'], order = '-create_time')

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
@args_required(['image_id', 'vcpu', 'mem'])
def create(args):
    '''创建虚拟机'''
    if 'net_type_id' not in args and 'vlan_id' not in args:
        return {'res': False, 'err': ERR_VM_CREATE_ARGS_VLAN}

    if 'group_id' not in args and 'host_id' not in args:
        return {'res': False, 'err': ERR_VM_CREATE_ARGS_HOST}
   
    optional_args = ['group_id', 'host_id', 'net_type_id', 'vlan_id', 'diskname', 'remarks', 'ipv4']

    kwargs = {}

    for field in optional_args:
        if field in args:
            kwargs[field] = args[field]
    
    api = VmAPI()
    vm = api.create_vm(args['image_id'], args['vcpu'], args['mem'], **kwargs)
   
    if vm == False:
        return {'res': False, 'err': ERR_VM_DEFINE}
    
    vm.set_creator(args['req_user'].username)
    # vm.start()
    uuid = vm.uuid
    return {'res':True,'uuid':uuid}

@api_log
@catch_error
@args_required('uuid')
def status(args):
    '''获取虚拟机状态'''
    api = VmAPI()
    vm = api.get_vm_by_uuid(args['uuid'])
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
    api = VmAPI()
    vm = api.get_vm_by_uuid(args['uuid'])
    if not vm:
        return {'res': False, 'err': ERR_VM_UUID}
    if not vm.can_operate_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}

    if args['op'] == 'delete':
        res = api.delete_vm(args['uuid'])
    elif args['op'] == 'delete_force':
        res = api.delete_vm(args['uuid'], force=True)
    elif args['op'] == 'reset':
        res = api.reset_vm(args['uuid'])
    else:   
        #虚拟机操作类型。 key,操作代码； value,VM对象中对应处理函数名称
        op_list = {
            'start': 'start', 
            'reboot': 'reboot', 
            'shutdown': 'shutdown', 
            'poweroff': 'poweroff'}
        
        if args['op'] in op_list:
            try:
                res = getattr(vm, op_list[args['op']]).__call__()
            except Error as e:
                return {'res': False, 'err': e.err}
            except Exception as e:
                raise e
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
    vcpu = None
    if 'vcpu' in args:
        try:
            vcpu = int(args['vcpu'])
        except: pass
    
    mem = None
    if 'mem' in args:
        try:
            mem = int(args['mem'])
        except: pass
    
    remarks = None
    if 'remarks' in args:
        remarks = args['remarks']

    api = VmAPI()
    vm = api.get_vm_by_uuid(args['uuid'])
    if not vm.can_operate_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
    res = api.edit_vm(args['uuid'], vcpu, mem, remarks)

    if res:
        return {'res': True}
    else:
        return {'res': False, 'err': ERR_VM_EDIT}
    
@api_log
@catch_error
@args_required(['uuid', 'host_id'])
def migrate(args):
    #被迁移虚拟机校验
    api = VmAPI()
    host_api = HostAPI()
    vm = api.get_vm_by_uuid(args['uuid'])
    if not vm:
        return {'res': False, 'err': ERR_VM_UUID}
    if not vm.can_operate_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
    
    #目标主机校验
    host = host_api.get_host_by_id(args['host_id'])
    if not host.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
    
    #被迁移虚拟机与目标主机是否处于同一个分中心
    if not vm.center_id == host.center_id:
        return {'res': False, 'err': ERR_AUTH_PERM}
    
    if vm.host_id == host.id:
        return {'res': False, 'err': ERR_VM_MIGRATE}
    
    res = api.migrate_vm(args['uuid'], args['host_id'])
    if res:
        return {'res': True}
    return {'res': False, 'err': ERR_VM_MIGRATE}

    