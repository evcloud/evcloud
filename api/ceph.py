#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2015-10-16
#@desc:    ceph相关的API函数，每一个函数封装并实现一个API接口的功能。
########################################################################

from compute.api import CenterAPI
from storage.api import CephStorageAPI
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
    ret_list = []
    storage_api = CephStorageAPI()
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
    '''获取ceph资源池列表'''
    ret_list = []
    api = CephStorageAPI()
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