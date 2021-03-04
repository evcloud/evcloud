from django.http import Http404
from django.core.exceptions import PermissionDenied
from rest_framework.views import set_rollback
from rest_framework.response import Response
from rest_framework.exceptions import (APIException, NotAuthenticated, AuthenticationFailed)

from utils import errors as exceptions


def exception_handler(exc, context):
    """
    Returns the response that should be used for any given exception.
    """
    if isinstance(exc, exceptions.Error):
        set_rollback()
        return Response(exc.data(), status=exc.status_code)

    if isinstance(exc, Http404):
        exc = exceptions.NotFoundError()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.AccessDeniedError()
    elif isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        exc = exceptions.AuthenticationFailedError()
    elif isinstance(exc, APIException):
        if isinstance(exc.detail, (list, dict)):
            data = exc.detail
        else:
            data = {'detail': exc.detail}

        exc = exceptions.Error(msg=str(data), code=exc.status_code)
    else:
        return None

    set_rollback()
    return Response(exc.data(), status=exc.status_code)
