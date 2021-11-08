from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import Serializer
from drf_yasg.utils import swagger_auto_schema
from compute.managers import CenterManager, GroupManager, ComputeError
from api.viewsets import CustomGenericViewSet


class ComputeQuotaViewSet(CustomGenericViewSet):
    """
    可用资源配额类视图
    """
    permission_classes = [IsAuthenticated]
    pagination_class = None
    lookup_field = 'id'

    @swagger_auto_schema(
        operation_summary='获取可用总资源配额和已用配额信息',
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
                "mem_reserved": 28392,
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
        quota = GroupManager().compute_quota(user=request.user)
        return Response(data={'quota': quota})

    def get_serializer_class(self):
        return Serializer
