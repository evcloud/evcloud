from django.shortcuts import render
from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.schemas import AutoSchema
from rest_framework.compat import coreapi, coreschema
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.serializers import Serializer

from vms.manager import VmManager, VmAPI
from vms.errors import VmError
from . import serializers

# Create your views here.
class CustomAutoSchema(AutoSchema):
    '''
    自定义Schema
    '''
    def get_manual_fields(self, path, method):
        '''
        重写方法，为每个方法自定义参数字段, action或method做key
        '''
        extra_fields = []
        action = None
        try:
            action = self.view.action
        except AttributeError:
            pass

        if action and type(self._manual_fields) is dict and action in self._manual_fields:
            extra_fields = self._manual_fields[action]
            return extra_fields

        if type(self._manual_fields) is dict and method in self._manual_fields:
            extra_fields = self._manual_fields[method]

        return extra_fields


class VmsViewSet(viewsets.GenericViewSet):
    '''
    虚拟机类视图
    '''
    permission_classes = [IsAuthenticated,]
    pagination_class = LimitOffsetPagination

    # api docs
    schema = CustomAutoSchema(
        manual_fields={
            # 'create': [
            #     coreapi.Field(
            #         name='image_id',
            #         location='form',
            #         required=True,
            #         schema=coreschema.Integer(description='系统镜像id')
            #     ),
            #     coreapi.Field(
            #         name='vcpu',
            #         location='form',
            #         required=True,
            #         schema=coreschema.Integer(description='cpu数')
            #     ),
            #     coreapi.Field(
            #         name='mem',
            #         location='form',
            #         required=True,
            #         schema=coreschema.Integer(description='内存大小')
            #     ),
            #     coreapi.Field(
            #         name='vlan_id',
            #         location='form',
            #         required=True,
            #         schema=coreschema.Integer(description='子网id')
            #     ),
            #     coreapi.Field(
            #         name='group_id',
            #         location='form',
            #         required=False,
            #         schema=coreschema.Integer(description='宿主机组id'),
            #         description='group_id or host_id required.'
            #     ),
            #     coreapi.Field(
            #         name='host_id',
            #         location='form',
            #         required=False,
            #         schema=coreschema.Integer(description='宿主机id'),
            #         description='group_id or host_id required.'
            #     ),
            #     coreapi.Field(
            #         name='remarks',
            #         location='form',
            #         required=False,
            #         schema=coreschema.String(description='备注信息')
            #     ),
            # ],
        }
    )

    def list(self, request, *args, **kwargs):
        manager = VmManager()
        self.queryset = manager.get_user_vms_queryset(user=request.user)

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            data = {'code': 200, 'vms': serializer.data, }
        return Response(data)

    def create(self, request, *args, **kwargs):
        code_text = ''
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=False):
            validated_data = serializer.validated_data
            api = VmAPI()
            try:
                vm = api.create_vm(user=request.user, **validated_data)
            except VmError as e:
                code_text = str(e)
            else:
                return Response(data={
                    'code': 201,
                    'code_text': '创建成功',
                    'data': request.data,
                    'vm': serializers.VmSerializer(vm).data
                }, status=status.HTTP_201_CREATED)

        if not code_text:
            code_text = '参数验证有误'
            try:
                for _, err_list in serializer.errors.items():
                    code_text = err_list[0]
            except:
                pass

        data = {
            'code': 400,
            'code_text': code_text,
            'data': serializer.data,
        }
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        Defaults to using `self.serializer_class`.
        Custom serializer_class
        """
        if self.action in ['list', 'retrieve']:
            return serializers.VmSerializer
        elif self.action =='create':
            return serializers.VmCreateSerializer
        return Serializer
