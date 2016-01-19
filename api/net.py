#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2015-10-16
#@desc:    分中心相关的API函数，每一个函数封装并实现一个API接口的功能。
########################################################################

from .tools import catch_error, args_required, api_log
from .error import ERR_AUTH_PERM, ERR_VLAN_NO_FIND, ERR_VLAN_ID, ERR_GROUP_ID

from compute.group import get_group
import network
from network import get_vlan_types

@api_log
@catch_error
@args_required('group_id')
def get_vlan_list(args=None):
    '''获取网络列表'''
    ret_list = []
    group = get_group(args['group_id'])
    if not group:
        return {'res': False, 'err': ERR_GROUP_ID}
    if not group.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}

    vlans = network.get_vlans(args['group_id'])
    
    if vlans:
        vlan_list = []
        for vlan in vlans:
            vlan_list.append({
                'id': vlan.id,
                'vlan': vlan.vlan,
                'br': vlan.br,
                'type_code': vlan.type_code,
                'type': vlan.type_name,
                'enable': vlan.enable,
                'order': vlan.order
                })
        return {'res': True, 'list': vlan_list}
    return {'res': False, 'err': ERR_VLAN_NO_FIND}


@api_log
@catch_error
@args_required('vlan_id')
def get_vlan(args=None):
    '''获取网络列表'''
    
    vlan = network.get_vlan(args['vlan_id'])
    if not vlan:
        return {'res': False, 'err': ERR_VLAN_ID}
    
    if not vlan.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
    
    return {'res': True,
            'info': {
                     'id': vlan.id,
                     'vlan': vlan.vlan,
                     'br': vlan.br,
                     'type_code': vlan.type_code,
                     'type_name': vlan.type_name,
                     'enable': vlan.enable}}

@api_log
@catch_error
def get_vlan_type_list():
    vlan_type_list = get_vlan_types()
    return {'res': True, 'list': vlan_type_list}