#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2015-10-16
#@desc:    ceph相关的API函数，每一个函数封装并实现一个API接口的功能。
########################################################################

from compute.api import CenterAPI
from storage.ceph import get_cephpools
from .tools import args_required, catch_error, print_process_time, api_log

from .error import ERR_AUTH_PERM, ERR_CENTER_ID

@api_log
@catch_error
@args_required('center_id')
def get_list(args):
    '''获取ceph资源池列表'''
    ret_list = []
    center_api = CenterAPI()
    if not center_api.center_id_exists(args['center_id']):
        return {'res': False, 'err': ERR_CENTER_ID}
    center = center_api.get_center_by_id(args['center_id'])
    
    if not center.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}

    pool_list = get_cephpools(args['center_id'])
        
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

