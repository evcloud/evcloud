#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2015-10-16
#@desc:    host device 相关接口
########################################################################

from device.api import GPUAPI
from compute.host import get_host
from compute.api import VmAPI
from .tools import args_required, catch_error, print_process_time, api_log

from .error import ERR_AUTH_PERM, ERR_GPU_EDIT_REMARKS, ERR_GPU_MOUNT, ERR_GPU_UMOUNT

@api_log
@catch_error
@args_required('host_id')
def get_gpu_list(args):
    host = get_host(args['host_id'])
    if not host.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
        
    api = GPUAPI()
    gpu_list = api.get_gpu_list_by_host_id(host.id)

    ret_list = []
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
    if not vm.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
    res = api.mount(args['vm_id'], args['gpu_id'])
    if res:
        return {'res': True}
    return {'res': False, 'err': ERR_GPU_MOUNT}

@api_log
@catch_error
@args_required(['gpu_id'])
def gpu_umount(args):
    api = GPUAPI()
    res = api.umount(args['gpu_id'])
    if res:
        return {'res': True}
    return {'res': False, 'err': ERR_GPU_UMOUNT}

