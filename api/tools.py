#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2015-10-16
#@desc:    虚拟机相关的API函数，每一个函数封装并实现一个API接口的功能。
########################################################################
import sys, json
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.conf import settings
from .error import ERR_ARGS_DECORATOR, ERR_ARGS_REQUIRED, ERR_PROCESS, ERR_LOG, ERR_AUTH_NO_LOGIN
from .error import Error
from vmuser.api import API as UserAPI

def get_args_from_get(req):
    '''从GET中获取所有参数'''
    args = {}
    for key in req.GET:
        args[key] = req.GET.get(key)
    args['req_user'] = req.user
    return args

def get_args_from_post(req):
    '''从POST中获取所有参数'''
    args = {}
    for key in req.POST:
        args[key] = req.POST.get(key)
    args['req_user'] = req.user
    args['__from_post'] = True
    return args

def check_args_exists(args, required_key):
    '''检查args中是否包含required_key中所要求的参数'''
    miss = []
    for r in required_key:
        if r not in args:
            miss.append(r)
    if miss == []:
        return True, ''
    return False, 'args %s required.' % ','.join(miss) 


#################################################装饰器#################################################

def args_required(required_keys=None):
    '''用于api函数的装饰器，检查被装饰函数的第一个参数时候包含指定参数'''
    if not required_keys:
        required_keys = []
    if type(required_keys) != list:
        required_keys = [required_keys]
    required_keys.append('req_user')
    def handle_func(func):
        def handle_args(*args, **kwargs):
            if len(args) < 1 or type(args[0]) != dict:
                return {'res': False, 'err': ERR_ARGS_DECORATOR}
            exists, err = check_args_exists(args[0], required_keys)
            if not exists:
                return {'res': False, 'err': ERR_ARGS_REQUIRED}
            # if not isinstance(args[0]['req_user'], User):
            #     return {'res': False, 'err': ERR_ARGS_REQUIRED}
            return func(*args, **kwargs)
        
        handle_args.__name__ = func.__name__
        handle_args.__module__ = func.__module__
        return handle_args
    return handle_func

def catch_error(func):
    def handle_args(*args, **kwargs): 
        try:
            return func(*args, **kwargs)  
        except Error as e:
            # print(e.err)
            if settings.DEBUG: 
                import traceback
                print(traceback.format_exc())
            return {'res': False, 'err': e.err} 
        # except Exception as e:
        #     if settings.DEBUG:
        #         import traceback
        #         print(traceback.format_exc())
        #
        #     return {'res': False, 'err':ERR_PROCESS}
        
    handle_args.__name__ = func.__name__
    handle_args.__module__ = func.__module__
    return handle_args

import time
def print_process_time(func):
    '''在控制台打印被装饰函数的执行时间。'''
    def handle_args(*args, **kwargs): 
        try:
            start_time = time.time()
            res = func(*args, **kwargs)
            end_time = time.time()
            print(func.__module__, func.__name__, ' process time: ', end_time - start_time)
            return res   
        except Exception as e:
            return {'res': False, 'err': ERR_PROCESS}
    handle_args.__name__ = func.__name__
    handle_args.__module__ = func.__module__
    return handle_args

from .models import Log
import datetime
def api_log(func):
    '''api 日志'''
    def handle_args(*args, **kwargs): 
        try:
            start_time = datetime.datetime.now()
            res = func(*args, **kwargs)
            end_time = datetime.datetime.now()
            if settings.DEBUG: print(func.__module__, func.__name__, ' process time: ', end_time - start_time)
            if len(args) > 0 and type(args[0]) == dict and 'req_user' in args[0]:
                try:
                    log = Log()
                    log.user = args[0]['req_user']
                    log.op = func.__module__ + '.' + func.__name__
                    log.start_time = start_time
                    log.finish_time = end_time
                    log.result = res['res']
                    log.from_trd_part = '__from_post' in args[0]
                    log.args = args
                    if not log.result:
                        error = ''
                        if 'err' in res:
                            error += res['err'] + ' '
                        if 'error' in res:
                            error += res['error']
                        log.error = error
                    log.save()
                except Exception as e:
                    print('[api_log error]', res)

            return res   
        except Exception as e:
            print(e)
            return {'res': False, 'err': str(e)}
    handle_args.__name__ = func.__name__
    handle_args.__module__ = func.__module__
    return handle_args

def login_required(func):
    '''api用户登录状态检测'''
    def handle_args(req, **kwargs): 
        try:
            session_id = req.POST.get('session_id')
            if settings.DEBUG: print('login required', session_id)
            if session_id:
                userapi = UserAPI()
                session = userapi.get_session_by_id(session_id)
                username = session.get(userapi.SESSION_KEY)
                ip = session.get(userapi.IP_SESSION_KEY)
                if settings.DEBUG: print('login required', username, ip)
                if ip == req.META['REMOTE_ADDR']:
                    user = User.objects.get(username = username)
                    req.user = user
                    return func(req, **kwargs)
        except Exception as e:
            if settings.DEBUG: print(e) 
        return HttpResponse(json.dumps({'res': False, 'err':ERR_AUTH_NO_LOGIN}))
        
    handle_args.__name__ = func.__name__
    handle_args.__module__ = func.__module__
    return handle_args
