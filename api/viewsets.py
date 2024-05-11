from django.http import Http404, HttpResponse
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework.views import set_rollback
from rest_framework.exceptions import (APIException, NotAuthenticated, AuthenticationFailed)

from utils import errors
from vms.models import ErrorLog


def exception_handler(exc, context):
    """
    Returns the response that should be used for any given exception.

    By default we handle the REST framework `APIException`, and also
    Django's built-in `Http404` and `PermissionDenied` exceptions.

    Any unhandled exceptions may return `None`, which will cause a 500 error
    to be raised.
    """

    if isinstance(exc, errors.APIIPAccessDeniedError):
        exc = errors.APIIPAccessDeniedError(msg=str(exc))
        data = exc.data()
        response = Response(data=data, status=exc.status_code)
        response.content = str(data)
        return response

    if isinstance(exc, errors.Error):
        set_rollback()
        return Response(exc.data(), status=exc.status_code)

    if isinstance(exc, Http404):
        exc = errors.NotFoundError()
    elif isinstance(exc, PermissionDenied):
        exc = errors.AccessDeniedError()
    elif isinstance(exc, AuthenticationFailed):
        exc = errors.AuthenticationFailedError()
    elif isinstance(exc, NotAuthenticated):
        exc = errors.NotAuthenticated()
    elif isinstance(exc, APIException):
        if isinstance(exc.detail, (list, dict)):
            data = exc.detail
        else:
            data = {'detail': exc.detail}

        exc = errors.Error(msg=str(data), code=exc.status_code, err_code=exc.default_code)
    else:
        exc = errors.Error(msg=str(exc))

    set_rollback()
    return Response(exc.data(), status=exc.status_code)


def log_err_response(request, response):
    """
    状态码>=400才记录
    """
    status_code = response.status_code
    method = request.method
    full_path = request.get_full_path()
    msg = f'{status_code} {method} {full_path}'
    err_msg = ''
    if 400 <= status_code:
        err_msg = response.data.get('message', '')
        code = response.data.get('code', '')
        if err_msg and code:
            err_msg = f'[{code}:{err_msg}]'
        if not err_msg:
            err_msg = f'{response.data}'

        msg = f'{msg} {err_msg}'

    username = ''
    if bool(request.user and request.user.is_authenticated):
        username = request.user.username

    ErrorLog.add_log(status_code=status_code, method=method, full_path=full_path, message=err_msg, username=username)


class CustomGenericViewSet(GenericViewSet):
    queryset = QuerySet().none()

    @staticmethod
    def exception_response(exc):
        if not isinstance(exc, errors.Error):
            exc = errors.Error(msg=str(exc))

        return Response(data=exc.data(), status=exc.status_code)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request=request, response=response, *args, **kwargs)
        # 如果是发生了异常，异常处理函数内已经记录了日志
        if getattr(response, 'exception', False):
            return response

        try:
            if response.status_code >= 400:
                log_err_response(request=request, response=response)
                # response._has_been_logged = True    # 告诉django已经记录过日志，不需再此记录了
        except Exception:
            pass

        return response