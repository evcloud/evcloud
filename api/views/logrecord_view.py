from datetime import datetime

from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import Serializer
from drf_yasg.utils import swagger_auto_schema

from api import serializers
from api.viewsets import CustomGenericViewSet
from drf_yasg import openapi

from logrecord.manager import user_operation_record


class LogRecordViewSet(CustomGenericViewSet):
    """
    可用资源配额类视图
    """
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination
    lookup_field = 'id'

    @swagger_auto_schema(
        operation_summary='获取用户操作日志',
        manual_parameters=[
            openapi.Parameter(
                name='timestamp',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description='时间戳'
            ),
            openapi.Parameter(
                name='username',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description='用户名称'
            ),
        ],
        responses={
            200: ''
        }
    )
    def list(self, request, *args, **kwargs):
        """
        获取用户操作日志

            http code 200:

                {
                  "create_time": "2024-04-08T15:28:39.091167+08:00",
                  "username": "wanghuang@cnic.cn",
                  "operation_content": "卸载硬盘"  #  操作内容
                }

        """

        timestamp = request.query_params.get('timestamp', '')
        username = request.query_params.get('username', '')

        if timestamp:
            timestamp = datetime.fromtimestamp(float(timestamp))  # 转datetime

        self.queryset = user_operation_record.get_log_record(username=username, timestamp=timestamp)

        # print(self.queryset)
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.LogRecordSerializer

        return Serializer
