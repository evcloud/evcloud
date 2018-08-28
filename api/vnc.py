#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2015-10-16
#@desc:    虚拟机相关的API函数，每一个函数封装并实现一个API接口的功能。
########################################################################

from .tools import args_required, catch_error, print_process_time, api_log
from novnc.vnc import VNC

@api_log
@catch_error
@args_required('uuid')
def open(args):
    vncmanager = VNC()
    info = vncmanager.set_token(args['uuid'])
    if info:
        return {'res': True, 'url': info['url'], 'vncid': str(info['id'])}
#     return {'res': False, 'error': vncmanager.error}
    raise RuntimeError(vncmanager.error)

@api_log
@catch_error
@args_required('vncid')
def close(args):
    vncmanager = VNC()
    if 'delay' in args and type(args['delay']) == int:
        res = vncmanager.del_token_delay(args['vncid'], args['delay'])
    else:
        res = vncmanager.del_token(args['vncid'])
#     return {'res': res}
    if res:
        return {'res': True}
    raise RuntimeError('close vnc error')