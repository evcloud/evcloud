from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response

from utils import errors


class CustomGenericViewSet(GenericViewSet):
    @staticmethod
    def exception_response(exc):
        if not isinstance(exc, errors.Error):
            exc = errors.Error(msg=str(exc))

        return Response(data=exc.data(), status=exc.status_code)
