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
                name='type',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description='类型（排除）：云主机,VPN,云硬盘,数据中心,宿主机,Vlan,镜像,用户,资源。使用,隔开'
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
                  "resourc_type": "云硬盘",   # 资源类型
                  "operation_content": "卸载硬盘"  #  操作内容
                }

        """

        # # 用户操作日志记录
        # user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.SELECT,
        #                               operation_content='查询云主机搁置列表', remark='')
        exclude_type = request.query_params.get('type', '')
        type_list = []
        if exclude_type:
            type_dict = {'云主机': 6, 'VPN': 7, '云硬盘': 8, '数据中心': 12, '宿主机': 13, 'Vlan': 14, '镜像': 15,
                         '用户': 16, '资源': 19}
            exclude_type = exclude_type.split(',')
            for log_type in exclude_type:
                if log_type in type_dict:
                    type_list.append(type_dict[log_type])

        self.queryset = user_operation_record.get_log_record(type_list=type_list)

        print(self.queryset)
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
