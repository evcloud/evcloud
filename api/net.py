#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2015-10-16
#@desc:    分中心相关的API函数，每一个函数封装并实现一个API接口的功能。
########################################################################

from .tools import catch_error
from .tools import args_required
from .tools import api_log
from .error import ERR_AUTH_PERM
from .error import ERR_VLAN_NO_FIND

from compute.api import GroupAPI
from network.api import NetworkAPI

@api_log
@catch_error
@args_required('group_id')
def get_vlan_list(args=None):
    '''获取网络列表'''
    ret_list = []
    group_api = GroupAPI()
    group = group_api.get_group_by_id(args['group_id'])

    if not group.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}

    network_api = NetworkAPI()
    vlans = network_api.get_vlan_list_by_group_id(args['group_id'])
    
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
                'order': vlan.order,
                'ip_count': vlan.ip_count,
                'ip_used': vlan.ip_used
                })
        return {'res': True, 'list': vlan_list}
    return {'res': False, 'err': ERR_VLAN_NO_FIND}


@api_log
@catch_error
@args_required('vlan_id')
def get_vlan(args=None):
    '''获取网络列表'''
    network_api = NetworkAPI()
    vlan = network_api.get_vlan_by_id(args['vlan_id'])
    
    if not vlan.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
    
    return {'res': True,
            'info': {
                     'id': vlan.id,
                     'vlan': vlan.vlan,
                     'br': vlan.br,
                     'type_code': vlan.type_code,
                     'type_name': vlan.type_name,
                     'enable': vlan.enable,
                    'ip_count': vlan.ip_count,
                    'ip_used': vlan.ip_used}}

@api_log
@catch_error
@args_required()
def get_vlan_type_list(args=None):
    network_api = NetworkAPI()
    try:
        vlan_type_list = network_api.get_vlan_type_list()
    except Exception as e:
        print(e)
    return {'res': True, 'list': vlan_type_list}