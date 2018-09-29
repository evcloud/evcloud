#coding=utf-8

########################################################################
#@author:   lzx
#@email:    lzxddz@cnic.cn
#@date:     2018-09-27
#@desc:    高可用监控记录相关的API函数，每一个函数封装并实现一个API接口的功能。
########################################################################

from monitoring.api import MonitoringAPI
from .tools import args_required
from .tools import catch_error
from .tools import api_log

from .error import ERR_AUTH_PERM


@api_log
@catch_error
@args_required('host_id')
def get_host_err_log_list(args):
    '''获取被监控的宿主机故障列表'''
    ret_list = []

    m_api = MonitoringAPI()
    h_log_list = m_api.get_host_error_log_list(host_id=args['host_id'])
            
    for h_log in h_log_list:
        ret_list.append({
            'id': h_log.id,
            'host_id': h_log.host_id,
            'host_ipv4': h_log.host_ipv4,
            'info': h_log.info,
            'create_time': h_log.create_time,
            'deleted': h_log.deleted
            })
    return {'res': True, 'list': ret_list}



@api_log
@catch_error
# @args_required('vm_uuid')
def get_vm_migrate_log_list(args):
    '''获取高可用监控中虚拟机迁移日志列表'''

    ret_list = []

    arg_vm_uuid = None
    arg_host_error_log_id = None

    if 'vm_uuid' in args:
        arg_vm_uuid = args['vm_uuid']
    if 'host_error_log_id' in args:
        arg_host_error_log_id = args['host_error_log_id']

    m_api = MonitoringAPI()
    vm_log_list = m_api.get_vm_migrate_log_list(vm_uuid=arg_vm_uuid,host_error_log_id=arg_host_error_log_id)
            
    for vm_log in vm_log_list:
        ret_list.append({
            'id':   vm_log.id,
            'host_error_log_id':vm_log.host_error_log_id,
            'vm_uuid':vm_log.vm_uuid,
            'vm_ipv4':vm_log.vm_ipv4,
            'src_host_ipv4':vm_log.src_host_ipv4,
            'dst_host_ipv4':vm_log.dst_host_ipv4,
            'migrate_res':vm_log.migrate_res,
            'info':vm_log.info,
            'create_time':vm_log.create_time,
            'deleted':vm_log.deleted,
            })
    return {'res': True, 'list': ret_list}