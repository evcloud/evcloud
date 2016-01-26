#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2015-10-16
#@desc:    宿主机集群相关的API函数，每一个函数封装并实现一个API接口的功能。
########################################################################

from compute.group import get_groups_in_perm, get_group
from .tools import args_required, catch_error, print_process_time, api_log

from .error import ERR_AUTH_PERM, ERR_GROUP_ID

@api_log
@catch_error
def get_list(args):
    '''获取集群列表'''
    ret_list = []
    
    if 'center_id' in args:
        group_list = get_groups_in_perm(args['req_user'], args['center_id'])
    else:
        group_list = get_groups_in_perm(args['req_user'])
            
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
    group = get_group(args['group_id'])
    if group == False:
        return {'res': False, 'err': ERR_GROUP_ID}
    if not group.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
    
    return {'res': True,
            'info': {
                'id':   group.id,
                'center_id': group.center_id,
                'name': group.name,
                'desc': group.desc,
                'admin_user': [user.username for user in group.admin_user]
                }
            }