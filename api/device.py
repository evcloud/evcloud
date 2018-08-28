#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2016-01-26
#@desc:    host device 相关接口
########################################################################

from device.api import GPUAPI
from compute.api import HostAPI
from compute.api import GroupAPI
from compute.api import VmAPI
from .tools import args_required
from .tools import catch_error
from .tools import api_log

from .error import ERR_AUTH_PERM
from .error import ERR_GPU_EDIT_REMARKS
from .error import ERR_GPU_MOUNT
from .error import ERR_GPU_UMOUNT
from .error import ERR_MOUNT_RUNNING
from .error import ERR_UMOUNT_RUNNING

@api_log
@catch_error
@args_required()
def get_gpu_list(args):
    group_api = GroupAPI()
    group_list = group_api.get_group_list_in_perm(args['req_user'])
    
    gpu_api = GPUAPI()
    ret_list = []

    for g in group_list:
        gpu_list = gpu_api.get_gpu_list_by_group_id(g.id)
        for gpu in gpu_list:
            ret_list.append({
                'id':   gpu.id,
                'host_ipv4': gpu.host_ipv4,
                'address': gpu.address,
                'vm': gpu.vm,
                'attach_time': gpu.attach_time,
                'enable': gpu.enable,
                'remarks': gpu.remarks})
    return {'res': True, 'list': ret_list}


# @api_log
# @catch_error
# @args_required('host_id')
# def get_gpu_list(args):
#     host_api = HostAPI()
#     host = host_api.get_host_by_id(args['host_id'])
#     if not host.managed_by(args['req_user']):
#         return {'res': False, 'err': ERR_AUTH_PERM}
        
#     gpu_api = GPUAPI()
#     gpu_list = gpu_api.get_gpu_list_by_host_id(host.id)

#     ret_list = []
#     for gpu in gpu_list:
#         ret_list.append({
#             'id':   gpu.id,
#             'host_ipv4': gpu.host_ipv4,
#             'address': gpu.address,
#             'vm': gpu.vm,
#             'attach_time': gpu.attach_time,
#             'enable': gpu.enable,
#             'remarks': gpu.remarks})
#     return {'res': True, 'list': ret_list}

@api_log
@catch_error
@args_required('gpu_id')
def get_gpu(args):
    api = GPUAPI()
    gpu = api.get_gpu_by_id(args['gpu_id'])
    if gpu.managed_by(args['req_user']):
        return {'res': True,
                'info':{
                    'id': gpu.id,
                    'host_ipv4': gpu.host_ipv4,
                    'host_id': gpu.host_id,
                    'address': gpu.address,
                    'vm': gpu.vm,
                    'attach_time': gpu.attach_time,
                    'enable': gpu.enable,
                    'remarks': gpu.remarks
                }}
    else:
        return {'res': False, 'err': ERR_AUTH_PERM}

@api_log
@catch_error
@args_required(['gpu_id', 'remarks'])
def set_gpu_remarks(args):
    api = GPUAPI()
    if api.set_remarks(args['gpu_id'], args['remarks']):
        return {'res': True}
    return {'res': False, 'err': ERR_GPU_EDIT_REMARKS}


@api_log
@catch_error
@args_required(['vm_id', 'gpu_id'])
def gpu_mount(args):
    api = GPUAPI()
    vm_api = VmAPI()
    vm = vm_api.get_vm_by_uuid(args['vm_id'])
    if not vm.can_operate_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
    if vm.is_running():
        return {'res': False, 'err': ERR_MOUNT_RUNNING}
    gpu = api.get_gpu_by_id(args['gpu_id'])
    if vm.group_id != gpu.group_id:
        return {'res': False, 'err': ERR_GPU_MOUNT}
    res = api.mount(args['vm_id'], args['gpu_id'])
    if res:
        return {'res': True}
    return {'res': False, 'err': ERR_GPU_MOUNT}

@api_log
@catch_error
@args_required(['gpu_id'])
def gpu_umount(args):
    api = GPUAPI()
    vm_api = VmAPI()
    gpu = api.get_gpu_by_id(args['gpu_id'])
    vm = vm_api.get_vm_by_uuid(gpu.vm)
    if not vm.can_operate_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
    if vm.is_running():
        return {'res': False, 'err': ERR_UMOUNT_RUNNING}
    res = api.umount(args['gpu_id'])
    if res:
        return {'res': True}
    return {'res': False, 'err': ERR_GPU_UMOUNT}

