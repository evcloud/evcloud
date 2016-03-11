#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2015-10-20
#@desc:    API用户验证相关的API函数
########################################################################

from .tools import catch_error
from .tools import args_required
from .error import ERR_AUTH_LOGIN
from .error import ERR_AUTH_LOGOUT
from vmuser.api import API


@catch_error
@args_required(['login_name', 'password', 'ip'])
def login(args):
    api = API()
    session_key = api.login(args['login_name'], args['password'], args['ip'])
    if session_key:
        return {'res': True, 'session_id': session_key}
    return {'res': False, 'err': ERR_AUTH_LOGIN}

@catch_error
@args_required(['session_id'])
def logout(args):
    api = API()
    res = api.logout(args['session_id'])
    if not res:
        return {'res': False, 'err': ERR_AUTH_LOGOUT}
    return {'res': True}

