from datetime import datetime

import pytz
from django.conf import settings
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

    @swagger_auto_schema(
        operation_summary='获取用户操作日志',
        manual_parameters=[
            openapi.Parameter(
                name='timestamp',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description='时间戳',
                default=0
            ),
            openapi.Parameter(
                name='direction',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=True,
                description='方向，时间戳之前的数据还是之后的数据',
                enum=['before', 'after'],
                default='after'
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
                      "create_time": 1714379004.22413,
                      "username": "test@cnic.cn",
                      "operation_content": "远程连接云主机vnc"
                    }

        """

        timestamp = request.query_params.get('timestamp', 0)
        username = request.query_params.get('username', '')
        direction = request.query_params.get('direction', 'after')

        dict_params = {}

        if username:
            dict_params['username'] = username

        timestamp = datetime.fromtimestamp(float(timestamp), tz=pytz.timezone(settings.TIME_ZONE))  # 转datetime
        if direction == 'before':
            dict_params['create_time__lte'] = timestamp
        else:
            dict_params['create_time__gt'] = timestamp

        order_by = "create_time"
        if direction == 'before':
            order_by = '-create_time'

        self.queryset = user_operation_record.get_log_records_order_by(order_by=order_by, kwargs=dict_params)

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
