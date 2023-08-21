from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import Serializer
from drf_yasg.utils import swagger_auto_schema
from compute.managers import CenterManager, GroupManager, ComputeError
from api.viewsets import CustomGenericViewSet
from drf_yasg import openapi
from utils import errors as exceptions


class ComputeQuotaViewSet(CustomGenericViewSet):
    """
    可用资源配额类视图
    """
    permission_classes = [IsAuthenticated]
    pagination_class = None
    lookup_field = 'id'

    @swagger_auto_schema(
        operation_summary='获取可用总资源配额和已用配额信息',
        manual_parameters=[
            openapi.Parameter(
                name='mem_unit',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description='内存计算单位（默认MB，可选GB）'
            )
        ],
        responses={
            200: ''
        }
    )
    def list(self, request, *args, **kwargs):
        """
        获取可用总资源配额和已用配额信息

            http code 200:
            {
              "quota": {
                "mem_total": 251552,            # Mb
                "mem_allocated": 4096,
                "vcpu_total": 292,
                "vcpu_allocated": 5,
                "real_cpu": 100,
                "vm_created": 3,
                "vm_limit": 41,
                "ips_total": 5,
                "ips_used": 2
              }
            }
        """
        mem_unit = str.upper(request.query_params.get('mem_unit', 'UNKNOWN'))
        if mem_unit not in ['GB', 'MB', 'UNKNOWN']:
            exc = exceptions.BadRequestError(msg='无效的内存单位, 正确格式为GB、MB或为空')
            return self.exception_response(exc)

        quota = GroupManager().compute_quota(user=request.user)
        if 'GB' == mem_unit:
            quota['mem_unit'] = 'GB'
        else:
            quota['mem_total'] = quota['mem_total'] * 1024
            quota['mem_allocated'] = quota['mem_allocated'] * 1024
            quota['mem_unit'] = 'MB'
        return Response(data={'quota': quota})

    def get_serializer_class(self):
        return Serializer
