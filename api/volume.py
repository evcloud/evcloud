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
from volume.api import VolumeAPI
from storage.api import get_storage_api
from compute.api import VmAPI
from compute.api import GroupAPI
from compute.api import HostAPI

@api_log
@catch_error
@args_required('volume_id')
def get(args):
    api = VolumeAPI()
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

    api = VolumeAPI()
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
@args_required([])
def get_volume_available(args):
    group_id = 'group_id' in args and args['group_id']
    vm_uuid = 'vm_uuid' in args and args['vm_uuid']
    user_id = 'user_id' in args and args['user_id']

    api = VolumeAPI()
    volume_list = api.get_volume_list(group_id=group_id, user_id=user_id)
    print('vmuuid=',vm_uuid)
    ret_list = []
    for volume in volume_list:
        if volume.managed_by(args['req_user']) and (volume.vm is None or (volume.vm and volume.vm == vm_uuid)):
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
@args_required(['size'])
def create(args):  # TODO: 乱
    backend = 'CEPH' #args.get('backend', 'CEPH')
    host_id = args.get('host_id')
    size = args.get('size')
    req_user = args['req_user']
    pool_id = args.get('pool_id')
    storage_api = get_storage_api(backend)
    api = VolumeAPI(storage_api=storage_api)

    res = True
    err = ''

    if backend == 'CEPH':
        group_id = args.get('group_id')
        group = GroupAPI().get_group_by_id(group_id)
        if not group.managed_by(req_user):
            err = '无权限操作'
            res = False
        if pool_id:
            pool = storage_api.get_pool_by_id(pool_id)
        else:
            pool = storage_api.get_volume_pool_by_center_id(group.center_id)
    # elif backend == 'GFS':
    #     host = HostAPI().get_host_by_id(host_id)
    #     if not host.managed_by(req_user):
    #         err = '无权限操作'
    #         res = False
    #     group_id = host.group_id

    #     # TODO: bad
    #     from storage.models import CephHost, CephPool
    #     h = CephHost.objects.filter(host=host.ipv4).first()
    #     p = CephPool.objects.filter(host=h).first()
    #     if p:
    #         pool = storage_api.get_pool_by_id(p.id)
    #     else:
    #         err = '宿主机无存储资源池'
    #         res = False
    else:
        err = '存储后端参数有误'
        res = False

    if res:
        # if not api.quota.group_quota_validate(group_id, size):
        #     err = '集群存储用量达到上限'
        #     res = False
        if not api.quota.group_pool_quota_validate(group_id, pool.id, size):
            err = '集群在存储卷上的存储用量达到上限'
            res = False

        # if not api.quota.volume_quota_validate(group_id, size):
        #     err = '超过单个云硬盘最大容量限制'
        #     res = False
        if not api.quota.volume_pool_quota_validate(group_id, pool.id, size):
            err = '超过存储卷允许的单个云硬盘最大容量限制'
            res = False

    if res:
        volume_id = api.create(pool.id, size, group_id)
        api.set_user_id(volume_id, args['req_user'].id)
        return {'res': True, 'volume_id': volume_id}

    return {'res': False, 'err': err}

@api_log
@catch_error
@args_required('volume_id')
def delete(args):
    api = VolumeAPI()

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
    api = VolumeAPI()
    vm_api = VmAPI()
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
    api = VolumeAPI()
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
    api = VolumeAPI()

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
    api = VolumeAPI()

    volume = api.get_volume_by_id(args['volume_id'])
    if not volume.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}

    res = api.set_remark(args['volume_id'], args['remarks'])
    if res:
        return {'res': True}
    return {'res': False, 'err': ERR_VOLUME_REMARKS}

@api_log
@catch_error
@args_required(['group_id'])
def get_quota_list(args):
    # if not args['req_user'].is_superuser:
    #     return {'res': False, 'err': ERR_AUTH_PERM}
    group_id = 'group_id' in args and args['group_id']    
    group = GroupAPI().get_group_by_id(group_id)
    if not group.managed_by(args['req_user']):
        return  {'res': False, 'err': ERR_AUTH_PERM}
    api = VolumeAPI()
    quota_list = api.quota.get_quota_list_by_group_id(group_id=group_id)
    ret_list = []
    for q in quota_list:
        ret_list.append({'id':q['id'],
                     'group_id':q['group_id'],
                     'cephpool_id':q['cephpool_id'],
                     'total_g':q['total_g'],
                     'volume_g':q['volume_g']})
    return {'res': True, 'list': ret_list}