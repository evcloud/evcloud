#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2016-01-27
#@desc:    
########################################################################

from .tools import args_required, catch_error, api_log
from .error import ERR_AUTH_PERM
from .error import ERR_IMAGE_ID
from .error import ERR_CEPH_ID
from .error import ERR_VOLUME_DELETE_DB
from .error import ERR_VOLUME_MOUNT
from .error import ERR_VOLUME_UMOUNT
from .error import ERR_VOLUME_RESIZE
from .error import ERR_VOLUME_REMARKS
from .error import ERR_MOUNT_RUNNING
from .error import ERR_UMOUNT_RUNNING
from volume.api import CephVolumeAPI
from compute.api import VmAPI
from compute.api import GroupAPI

@api_log
@catch_error
@args_required('volume_id')
def get(args):
    api = CephVolumeAPI()
    volume = api.get_volume_by_id(args['volume_id'])
    if not volume.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
    return {
        'res': True,
        'info': {
            'id': volume.id,
            'user_id': volume.user_id,
            'user_name': volume.user_name,
            'group_id': volume.group_id,
            'create_time': volume.create_time,
            'size': volume.size,
            'remarks': volume.remarks,
            'vm': volume.vm,
            'attach_time': volume.attach_time,
            'dev': volume.dev,
            'enable': volume.enable,
            'cephpool_id': volume.cephpool_id
        }
    }

@api_log
@catch_error
@args_required([])
def get_list(args):
    group_id = 'group_id' in args and args['group_id']
    cephpool_id = 'cephpool_id' in args and args['cephpool_id']
    user_id = 'user_id' in args and args['user_id']
    vm_uuid = 'vm_uuid' in args and args['vm_uuid']

    api = CephVolumeAPI()
    volume_list = api.get_volume_list(group_id=group_id, cephpool_id=cephpool_id, user_id=user_id, vm_uuid=vm_uuid)
    ret_list = []
    for volume in volume_list:
        if volume.managed_by(args['req_user']):
            ret_list.append({
                'id': volume.id,
                'user_id': volume.user_id,
                'user_name': volume.user_name,
                'group_id': volume.group_id,
                'group_name': volume.group_name,
                'create_time': volume.create_time,
                'size': volume.size,
                'remarks': volume.remarks,
                'vm': volume.vm,
                'attach_time': volume.attach_time,
                'dev': volume.dev,
                'enable': volume.enable,
                'cephpool_id': volume.cephpool_id
            })
    return {'res': True, 'list': ret_list}

@api_log
@catch_error
@args_required(['group_id', 'size'])
def create(args):
    api = CephVolumeAPI()
    group_api = GroupAPI()
    group = group_api.get_group_by_id(args['group_id'])
    if not group.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
    volume_id = api.create(args['group_id'], args['size'])
    api.set_user_id(volume_id, args['req_user'].id)
    return {'res': True, 'volume_id': volume_id}

@api_log
@catch_error
@args_required('volume_id')
def delete(args):
    api = CephVolumeAPI()

    volume = api.get_volume_by_id(args['volume_id'])
    if not volume.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
    
    del_success = api.delete(args['volume_id'])
    if del_success:
        return {'res': True}
    else:
        return {'res': False, 'err': ERR_VOLUME_DELETE_DB}
    
@api_log
@catch_error
@args_required(['vm_uuid', 'volume_id'])
def mount(args):
    api = CephVolumeAPI()
    vm_api=  VmAPI()

    vm = vm_api.get_vm_by_uuid(args['vm_uuid'])
    if not vm.can_operate_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
    if vm.is_running():
        return {'res': False, 'err': ERR_MOUNT_RUNNING}
    
    volume = api.get_volume_by_id(args['volume_id'])
    if not volume.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}

    res = api.mount(args['vm_uuid'], args['volume_id'])
    if res:
        return {'res': True}
    return {'res': False, 'err': ERR_VOLUME_MOUNT}

@api_log
@catch_error
@args_required('volume_id')
def umount(args):
    api = CephVolumeAPI()
    vm_api = VmAPI()

    volume = api.get_volume_by_id(args['volume_id'])
    if not volume.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}

    vm = vm_api.get_vm_by_uuid(volume.vm)
    if not vm.can_operate_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}

    if vm.is_running():
        return {'res': False, 'err': ERR_UMOUNT_RUNNING}

    res = api.umount(args['volume_id'])
    if res:
        return {'res': True}
    return {'res': False, 'err': ERR_VOLUME_UMOUNT}

@api_log
@catch_error
@args_required(['volume_id', 'size'])
def resize(args):
    api = CephVolumeAPI()

    volume = api.get_volume_by_id(args['volume_id'])
    if not volume.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}

    res = api.resize(args['volume_id'], args['size'])
    if res:
        return {'res': True}
    return {'res': False, 'err': ERR_VOLUME_RESIZE}

@api_log
@catch_error
@args_required(['volume_id', 'remarks'])
def set_remark(args):
    api = CephVolumeAPI()

    volume = api.get_volume_by_id(args['volume_id'])
    if not volume.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}

    res = api.set_remark(args['volume_id'], args['remarks'])
    if res:
        return {'res': True}
    return {'res': False, 'err': ERR_VOLUME_REMARKS}
