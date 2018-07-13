#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2015-10-16
#@desc:    ceph相关的API函数，每一个函数封装并实现一个API接口的功能。
########################################################################

from compute.api import CenterAPI,GroupAPI
from storage.api import StorageAPI
from volume.api import VolumeAPI
from storage.api import CEPH_IMAGE_POOL_FLAG
from storage.api import CEPH_VOLUME_POOL_FLAG
from .tools import args_required
from .tools import catch_error
from .tools import api_log

from .error import ERR_AUTH_PERM
from .error import ERR_CENTER_ID
from .error import ERR_CEPHPOOL_ID


@api_log
@catch_error
@args_required('center_id')
def get_list(args):
    '''获取ceph资源池列表'''
    #如果参数中有group_id，则返回group可用的ceph资源列表
    if 'group_id' in args and args['group_id']:
        return _get_pool_list_by_group_id(args)
    ret_list = []
    storage_api = StorageAPI()
    center_api = CenterAPI()
    if not center_api.center_id_exists(args['center_id']):
        return {'res': False, 'err': ERR_CENTER_ID}
    center = center_api.get_center_by_id(args['center_id'])    
    try:        
        if not center.managed_by(args['req_user']):
            return {'res': False, 'err': ERR_AUTH_PERM}

        pool_list = storage_api.get_pool_list_by_center_id(args['center_id'])
    except Exception as e:
        print(e)
        raise e    
    for pool in pool_list:
        ret_list.append({
            'id':   pool.id,
            'pool': pool.pool,
            'type': pool.type,
            'center_id': pool.center_id,
            'host': pool.host,
            'port': pool.port,
            'uuid': pool.uuid
            })

    return {'res': True, 'list': ret_list}

@api_log
@catch_error
@args_required('cephpool_id')
def get(args):
    '''获取ceph资源池信息'''
    ret_list = []
    api = StorageAPI()
    try:
        pool = api.get_pool_by_id(args['cephpool_id'])
        if not pool.managed_by(args['req_user']):
            return {'res': False, 'err': ERR_AUTH_PERM}
    except Exception as e:
        print(e)

    if pool:
        return {
            'res': True, 
            'info':{
                'id':   pool.id,
                'pool': pool.pool,
                'type': pool.type,
                'center_id': pool.center_id,
                'host': pool.host,
                'port': pool.port,
                'uuid': pool.uuid
                }
            }

    return {'res': False, 'err': ERR_CEPHPOOL_ID}



def _get_pool_list_by_group_id(args):
    '''获取指定计算集群（group）可使用的ceph资源池列表,即根据group可用的quota进行筛选'''
    ret_list = []
    storage_api = StorageAPI()
    center_api = CenterAPI()
    volume_api = VolumeAPI()

    group_id = 'group_id' in args and args['group_id']
    print(group_id)
    group = GroupAPI().get_group_by_id(group_id)
    if not group.managed_by(args['req_user']):
        return  {'res': False, 'err': ERR_AUTH_PERM}
    
    quota_list = volume_api.quota.get_quota_list_by_group_id(group_id=group_id)
    print(quota_list)
    pool_list = []
    for q in quota_list:
        if not q['cephpool_id']:
            continue 
        try:
            pool = storage_api.get_pool_by_id(q['cephpool_id'])            
            pool_list.append(pool)            
        except Exception as e:
            print(e)
    
    for pool in pool_list:
        ret_list.append({
            'id':   pool.id,
            'pool': pool.pool,
            'type': pool.type,
            'center_id': pool.center_id,
            'host': pool.host,
            'port': pool.port,
            'uuid': pool.uuid
            })

    return {'res': True, 'list': ret_list}