#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2015-10-20
#@desc:    API用户验证相关的API函数
########################################################################

from .tools import catch_error, args_required

from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.forms import AuthenticationForm

from django.contrib.sessions.backends.cached_db import SessionStore
from .error import ERR_AUTH_LOGIN, ERR_AUTH_LOGOUT

SESSION_KEY = '_auth_user'
IP_SESSION_KEY = '_auth_ip'

def get_session_by_id(session_id=None):
    session = SessionStore(session_id)
    return session

@catch_error
@args_required(['login_name', 'password', 'ip'])
def login(args):
    session = get_session_by_id()
    user = authenticate(username = args['login_name'], password = args['password'])
    if user and user.api_user:
        session[SESSION_KEY] = user.username
        session[IP_SESSION_KEY] = args['ip']
        if 'expiry' in args and args['expiry'].isdigit():
            session.set_expiry(int(args['expiry']))
        else:
            session.set_expiry(86400)
        session.save()
        return {'res': True, 'session_id': session._session_key}
    return {'res': False, 'err': ERR_AUTH_LOGIN}

@catch_error
def logout(args):
    try:
        session = get_session_by_id(args['session_id'])
        session.delete()
    except Exception as e:
        return {'res': False, 'err': ERR_AUTH_LOGOUT}
    return {'res': True}

