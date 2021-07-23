from django.http import Http404
from django.core.exceptions import PermissionDenied
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework.views import set_rollback
from rest_framework.exceptions import (APIException, NotAuthenticated, AuthenticationFailed)

from utils import errors


def exception_handler(exc, context):
    """
    Returns the response that should be used for any given exception.

    By default we handle the REST framework `APIException`, and also
    Django's built-in `Http404` and `PermissionDenied` exceptions.

    Any unhandled exceptions may return `None`, which will cause a 500 error
    to be raised.
    """
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


class CustomGenericViewSet(GenericViewSet):
    @staticmethod
    def exception_response(exc):
        if not isinstance(exc, errors.Error):
            exc = errors.Error(msg=str(exc))

        return Response(data=exc.data(), status=exc.status_code)
