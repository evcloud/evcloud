#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2015-10-16
#@desc:    宿主机相关的API函数，每一个函数封装并实现一个API接口的功能。
########################################################################

from compute.host import get_host, get_hosts
from compute.group import get_group
from .tools import args_required, catch_error, print_process_time, api_log
from .error import ERR_HOST_ID, ERR_AUTH_PERM, ERR_GROUP_ID

@api_log
@catch_error
@args_required('host_id')
def get(args):
    host = get_host(args['host_id'])
    if not host:
        return {'res': False, 'err': ERR_HOST_ID}
    
    if not host.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
     
    return {'res': True,
            'info': {
                     'id': host.id,
                     'vlan_list': host.vlans,
                     'ipv4': host.ipv4,
                     'vcpu_total': host.vcpu_total,
                     'vcpu_allocated': host.vcpu_allocated,
                     'mem_total': host.mem_total,
                     'mem_allocated': host.mem_allocated,
                     'mem_reserved': host.mem_reserved,
                     'vm_limit': host.vm_limit,
                     'vm_created': host.vm_created,
                     'enable': host.enable
                     }}

@api_log
@catch_error
@args_required('group_id')
def get_list(args):
    '''获取宿主机列表'''
    ret_list = []
    group = get_group(args['group_id'])
    if not group:
        return {'res': False, 'err': ERR_GROUP_ID}
    if not group.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
     
    host_list = get_hosts(args['group_id'])
     
    for host in host_list:
        ret_list.append({
            'id':   host.id,
            'group_id': host.group_id,
            'ipv4': host.ipv4,
            'vcpu_total': host.vcpu_total,
            'vcpu_allocated': host.vcpu_allocated,
            'mem_total': host.mem_total,
            'mem_allocated': host.mem_allocated,
            'mem_reserved': host.mem_reserved,
            'vm_limit': host.vm_limit,
            'vm_created': host.vm_created,
            'enable': host.enable,
            'net_types':[vlan[1] for vlan in host.vlan_types]})
    return {'res': True, 'list': ret_list}