import logging

from django.http.request import HttpRequest
from rest_framework.request import Request

logger_user = logging.getLogger('user')
def log_user(msg=''):
    '''
    用户操作日志记录装饰器
    用于API视图函数上，记录用户，url，method等信息
    '''
    def decorator(func):
        def wrapper(*args, **kwargs):
            ret = func(*args, **kwargs)
            try:
                for r in args:
                    if isinstance(r, HttpRequest) or isinstance(r, Request):
                        user = r.user
                        user_id = user.id if user.id else 0
                        username = user.username
                        url = r.get_full_path()
                        method = r.method
                        logger_user.info(msg=msg, extra={'user_id': user_id, 'username': username, 'url': url, 'method': method})
                        break
            except Exception as e:
                pass

            return ret
        return wrapper
    return decorator




