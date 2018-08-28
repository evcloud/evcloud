#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2015-10-16
#@desc:    宿主机集群相关的API函数，每一个函数封装并实现一个API接口的功能。
########################################################################

from compute.api import GroupAPI
from .tools import args_required
from .tools import catch_error
from .tools import api_log

from .error import ERR_AUTH_PERM

@api_log
@catch_error
def get_list(args):
    '''获取集群列表'''
    ret_list = []
    group_api = GroupAPI()
    
    if 'center_id' in args:
        group_list = group_api.get_group_list_in_perm(args['req_user'].username, args['center_id'])
    else:
        group_list = group_api.get_group_list_in_perm(args['req_user'].username)
            
    for group in group_list:
        ret_list.append({
            'id':   group.id,
            'center_id': group.center_id,
            'name': group.name,
            'desc': group.desc,
            'admin_user': [user.username for user in group.admin_user],
            'order': group.order})
    return {'res': True, 'list': ret_list}


@api_log
@catch_error
@args_required('group_id')
def get(args):    
    group_api = GroupAPI()
    group = group_api.get_group_by_id(args['group_id'])

    if not group.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
    
    return {'res': True,
            'info': {
                'id':   group.id,
                'center_id': group.center_id,
                'name': group.name,
                'desc': group.desc,
                'admin_user': [user.username for user in group.admin_user],
                'order': group.order
                }
            }