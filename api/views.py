from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.schemas import AutoSchema
from rest_framework.compat import coreapi, coreschema
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.serializers import Serializer
from rest_framework.decorators import action
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

from vms.manager import VmManager, VmAPI, VmError
from novnc.manager import NovncTokenManager, NovncError
from compute.models import Center, Group, Host
from compute.managers import CenterManager, HostManager, ComputeError
from network.models import Vlan, MacIP
from image.models import Image
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

    list:
        虚拟机列表

        >> http code 200:
        {
          "count": 2,
          "next": null,
          "previous": null,
          "results": [
            {
              "uuid": "4c0cdba7fe97405bac174baa03f3d036",
              "name": "4c0cdba7fe97405bac174baa03f3d036",
              "vcpu": 2,
              "mem": 2048,
              "disk": "4c0cdba7fe97405bac174baa03f3d036",
              "host": "10.100.50.121",
              "mac_ip": "10.107.50.252",
              "user": {
                "id": 3,
                "username": "test"
              },
              "create_time": "2019-10-11 07:03:44"
            },
          ]
        }

    create:
        创建虚拟机

        >> http code 201: 创建成功
        {
          "code": 201,
          "code_text": "创建成功",
          "data": { },              # 请求时提交的数据
          "vm": {
            "uuid": "4c0cdba7fe97405bac174baa03f3d036",
            "name": "4c0cdba7fe97405bac174baa03f3d036",
            "vcpu": 2,
            "mem": 2048,
            "disk": "4c0cdba7fe97405bac174baa03f3d036",
            "host": "10.100.50.121",
            "mac_ip": "10.107.50.252",
            "user": {
              "id": 3,
              "username": "test"
            },
            "create_time": "2019-10-11 07:03:44"
          }
        }
        >> http code 200: 创建失败
        {
          "code": 200,
          "code_text": "创建失败",
          "data": { },              # 请求时提交的数据
        }
        >>Http Code: 状态码400：请求数据有误;
            {
                'code': 400,
                'code_text': '请求数据有误'
            }

    destroy:
        删除虚拟机

        >> Http Code: 状态码204：删除成功，NO_CONTENT；
        >>Http Code: 状态码200：请求成功，未能成功删除虚拟机;
            {
                'code': 200,
                'code_text': '删除虚拟机失败'
            }
        >>Http Code: 状态码400：文件路径参数有误：对应参数错误信息;
            {
                'code': 400,
                'code_text': '参数有误'
            }
        >>Http Code: 状态码404：找不到资源;
        >>Http Code: 状态码500：服务器内部错误;

    retrieve:
        获取虚拟机元数据信息

        http code: 200, 请求成功：
        {
          "code": 200,
          "code_text": "获取虚拟机信息成功",
          "vm": {
            "uuid": "5b1f9a09b7224bdeb2ae12678ad0b1d4",
            "name": "5b1f9a09b7224bdeb2ae12678ad0b1d4",
            "vcpu": 2,
            "mem": 2048,
            "disk": "5b1f9a09b7224bdeb2ae12678ad0b1d4",
            "host": "10.100.50.121",
            "mac_ip": "10.107.50.253",
            "user": {
              "id": 1,
              "username": "shun"
            },
            "create_time": "2019-10-12 08:09:27"
          }
        }
        >>Http Code: 状态码400：请求失败;
            {
                'code': 400,
                'code_text': 'xxx失败'
            }

    vm_operations:
        操作虚拟机

        >>Http Code: 状态码200：请求成功;
            {
                'code': 200,
                'code_text': '操作虚拟机成功'
            }
        >>Http Code: 状态码400：请求失败;
            {
                'code': 400,
                'code_text': '操作虚拟机失败'
            }

    vm_status:
        获取虚拟机当前运行状态

        >> http code 200, 成功：
        {
          "code": 200,
          "code_text": "获取信息成功",
          "status": {
            "status_code": 5,
            "status_text": "shut off"
          }
        }

    partial_update:
        修改虚拟机vcpu和内存大小

    '''
    permission_classes = [IsAuthenticated,]
    pagination_class = LimitOffsetPagination
    lookup_field = 'uuid'
    lookup_value_regex = '[0-9a-z-]+'

    # api docs
    schema = CustomAutoSchema(
        manual_fields={
            'list': [
                coreapi.Field(
                    name='center_id',
                    location='query',
                    required=False,
                    schema=coreschema.Integer(description='分中心id'),
                    description='所属分中心'
                ),
                coreapi.Field(
                    name='group_id',
                    location='query',
                    required=False,
                    schema=coreschema.Integer(description='宿主机组id'),
                    description='所属宿主机组'
                ),
                coreapi.Field(
                    name='host_id',
                    location='query',
                    required=False,
                    schema=coreschema.Integer(description='宿主机id'),
                    description='所属宿主机'
                ),
                coreapi.Field(
                    name='search',
                    location='query',
                    required=False,
                    schema=coreschema.String(description='关键字'),
                    description='关键字查询'
                )
            ],
            'destroy': [
                coreapi.Field(
                    name='force',
                    location='query',
                    required=False,
                    schema=coreschema.Boolean(description='强制删除'),
                    description='true:强制删除'
                ),
            ],
            'vm_operations': [
                coreapi.Field(
                    name='op',
                    location='form',
                    required=True,
                    schema=coreschema.Enum(enum=['start', 'reboot', 'shutdown', 'poweroff', 'delete', 'delete_force'], description='操作'),
                    description="选项：['start', 'reboot', 'shutdown', 'poweroff', 'delete', 'delete_force']"
                ),
            ],
            'vm_remark': [
                coreapi.Field(
                    name='remark',
                    location='query',
                    required=True,
                    schema=coreschema.String(description='备注信息'),
                    description='新的备注信息'
                ),
            ]
        }
    )

    def list(self, request, *args, **kwargs):
        center_id = int(request.query_params.get('center_id', 0))
        group_id = int(request.query_params.get('group_id', 0))
        host_id = int(request.query_params.get('host_id', 0))
        search = request.query_params.get('search', '')

        manager = VmManager()
        try:
            self.queryset = manager.filter_vms_queryset(center_id=center_id, group_id=group_id, host_id=host_id,
                                                    search=search, user_id=request.user.id)
        except VmError as e:
            return Response(data={'code': 400, 'code_text': '查询虚拟机时错误'}, status=status.HTTP_400_BAD_REQUEST)

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
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid(raise_exception=False):
            code_text = '参数验证有误'
            try:
                for name, err_list in serializer.errors.items():
                    code_text = f'"{name}" {err_list[0]}'
            except:
                pass

            data = {
                'code': 400,
                'code_text': code_text,
                'data': serializer.data,
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        api = VmAPI()
        try:
            vm = api.create_vm(user=request.user, **validated_data)
        except VmError as e:
            data = {
                'code': 200,
                'code_text': str(e),
                'data': serializer.data,
            }
            return Response(data, status=status.HTTP_200_OK)

        return Response(data={
            'code': 201,
            'code_text': '创建成功',
            'data': request.data,
            'vm': serializers.VmSerializer(vm).data
        }, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        vm_uuid = kwargs.get(self.lookup_field, '')
        try:
            vm = VmManager().get_vm_by_uuid(uuid=vm_uuid)
        except VmError as e:
            return  Response(data={'code': 500, 'code_text': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not vm:
            return Response(data={'code': 404, 'code_text': '虚拟机不存在'}, status=status.HTTP_404_NOT_FOUND)
        if not vm.user_has_perms(user=request.user):
            return Response(data={'code': 404, 'code_text': '当前用户没有权限访问此虚拟机'}, status=status.HTTP_404_NOT_FOUND)

        return Response(data={
            'code': 200,
            'code_text': '获取虚拟机信息成功',
            'vm': serializers.VmSerializer(vm).data
        })

    def destroy(self, request, *args, **kwargs):
        vm_uuid = kwargs.get(self.lookup_field, '')
        force = request.query_params.get('force', '').lower()
        force = True if force == 'true' else False

        api = VmAPI()
        try:
             api.delete_vm(user=request.user, vm_uuid=vm_uuid, force=force)
        except VmError as e:
            return Response(data={'code': 200, 'code_text': f'删除失败，{str(e)}'}, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_204_NO_CONTENT)

    def partial_update(self, request, *args, **kwargs):
        vm_uuid = kwargs.get(self.lookup_field, '')

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid(raise_exception=False):
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

        validated_data = serializer.validated_data
        vcpu = validated_data.get('vcpu', 0)
        mem = validated_data.get('mem', 0)

        api = VmAPI()
        try:
            ok = api.edit_vm_vcpu_mem(user=request.user, vm_uuid=vm_uuid, mem=mem, vcpu=vcpu)
        except VmError as e:
            return Response(data={'code': 400, 'code_text': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if not ok:
            return Response(data={'code': 400, 'code_text': '修改虚拟机失败'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data={'code': 200, 'code_text': '修改虚拟机成功'})

    @action(methods=['patch'], url_path='operations', detail=True, url_name='vm_operations')
    def vm_operations(self, request, *args, **kwargs):
        vm_uuid = kwargs.get(self.lookup_field, '')
        try:
            op = request.data.get('op', None)
        except Exception as e:
            return Response(data={'code': 400, 'code_text': f'参数有误，{str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        ops = ['start', 'reboot', 'shutdown', 'poweroff', 'delete', 'delete_force']
        if not op or op not in ops:
            return Response(data={'code': 400, 'code_text': 'op参数无效'}, status=status.HTTP_400_BAD_REQUEST)

        api = VmAPI()
        try:
            ok = api.vm_operations(user=request.user, vm_uuid=vm_uuid, op=op)
        except VmError as e:
            return Response(data={'code': 400, 'code_text': f'{op}虚拟机失败，{str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        if not ok:
            return Response(data={'code': 400, 'code_text': f'{op}虚拟机失败'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data={'code': 200, 'code_text': f'{op}虚拟机成功'})

    @action(methods=['get'], url_path='status', detail=True, url_name='vm_status')
    def vm_status(self, request, *args, **kwargs):
        vm_uuid = kwargs.get(self.lookup_field, '')
        api = VmAPI()
        try:
            code, msg = api.get_vm_status(user=request.user, vm_uuid=vm_uuid)
        except VmError as e:
            return Response(data={'code': 400, 'code_text': f'获取虚拟机状态失败，{str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data={'code': 200, 'code_text': '获取信息成功',
                              'status': {'status_code': code, 'status_text': msg}})

    @action(methods=['post'], url_path='vnc', detail=True, url_name='vm_vnc')
    def vm_vnc(self, request, *args, **kwargs):
        '''
        创建虚拟机vnc

            >> http code 200:
            {
              "code": 200,
              "code_text": "创建虚拟机vnc成功",
              "vnc": {
                "id": "42bfe71e-6419-474a-bc99-9e519637797d",
                "url": "http://159.226.91.140:8000/novnc/?vncid=42bfe71e-6419-474a-bc99-9e519637797d"
              }
            }
        '''
        vm_uuid = kwargs.get(self.lookup_field, '')
        try:
            vm = VmManager().get_vm_by_uuid(uuid=vm_uuid)
        except VmError as e:
            return Response(data={'code': 500, 'code_text': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not vm:
            return Response(data={'code': 404, 'code_text': '虚拟机不存在'}, status=status.HTTP_404_NOT_FOUND)
        if not vm.user_has_perms(user=request.user):
            return Response(data={'code': 404, 'code_text': '当前用户没有权限访问此虚拟机'}, status=status.HTTP_404_NOT_FOUND)

        vm_uuid = vm.get_uuid()
        host_ipv4 = vm.host.ipv4

        vnc_manager = NovncTokenManager()
        try:
            vnc_id, url = vnc_manager.generate_token(vmid=vm_uuid, hostip=host_ipv4)
        except NovncError as e:
            return Response(data={'code': 400, 'code_text': f'创建虚拟机vnc失败，{str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        url = request.build_absolute_uri(url)
        return Response(data={'code': 200, 'code_text': '创建虚拟机vnc成功',
                              'vnc': {'id': vnc_id, 'url': url}})

    @action(methods=['patch'], url_path='remark', detail=True, url_name='vm_remark')
    def vm_remark(self, request, *args, **kwargs):
        '''
        修改虚拟机备注信息
        '''
        remark = request.query_params.get('remark')
        if not remark:
            return Response(data={'code': 400, 'code_text': '参数有误，无效的备注信息'}, status=status.HTTP_400_BAD_REQUEST)

        vm_uuid = kwargs.get(self.lookup_field, '')
        api = VmAPI()
        try:
            api.modify_vm_remark(user=request.user, vm_uuid=vm_uuid, remark=remark)
        except VmError as e:
            return Response(data={'code': 400, 'code_text': f'修改虚拟机备注信息失败，{str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data={'code': 200, 'code_text': '修改虚拟机备注信息成功'})

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        Defaults to using `self.serializer_class`.
        Custom serializer_class
        """
        if self.action in ['list', 'retrieve']:
            return serializers.VmSerializer
        elif self.action == 'create':
            return serializers.VmCreateSerializer
        elif self.action == 'partial_update':
            return serializers.VmPatchSerializer
        return Serializer


class CenterViewSet(viewsets.GenericViewSet):
    '''
    分中心类视图
    '''
    permission_classes = [IsAuthenticated, ]
    pagination_class = LimitOffsetPagination
    queryset = Center.objects.all()

    # api docs
    schema = CustomAutoSchema(
        manual_fields={
        }
    )
    def list(self, request, *args, **kwargs):
        '''
        获取分中心列表
        '''
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        Defaults to using `self.serializer_class`.
        Custom serializer_class
        """
        if self.action in ['list', 'retrieve']:
            return serializers.CenterSerializer
        return Serializer


class GroupViewSet(viewsets.GenericViewSet):
    '''
    宿主机组类视图
    '''
    permission_classes = [IsAuthenticated, ]
    pagination_class = LimitOffsetPagination
    queryset = Group.objects.all()

    # api docs
    schema = CustomAutoSchema(
        manual_fields={
        }
    )

    def list(self, request, *args, **kwargs):
        '''
        获取宿主机组列表
        '''
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        Defaults to using `self.serializer_class`.
        Custom serializer_class
        """
        if self.action in ['list', 'retrieve']:
            return serializers.GroupSerializer
        return Serializer


class HostViewSet(viewsets.GenericViewSet):
    '''
    宿主机类视图
    '''
    permission_classes = [IsAuthenticated, ]
    pagination_class = LimitOffsetPagination
    queryset = Host.objects.all()

    # api docs
    schema = CustomAutoSchema(
        manual_fields={
            'list': [
                coreapi.Field(
                    name='group_id',
                    location='query',
                    required=False,
                    schema=coreschema.Integer(description='宿主机组id'),
                    description='所属宿主机组'
                ),
                coreapi.Field(
                    name='vlan_id',
                    location='query',
                    required=False,
                    schema=coreschema.Integer(description='子网网段id'),
                    description='所属子网网段'
                )
            ]
        }
    )

    def list(self, request, *args, **kwargs):
        '''
        获取宿主机列表

            http code 200:
            {
              "count": 1,
              "next": null,
              "previous": null,
              "results": [
                {
                  "id": 1,
                  "ipv4": "10.100.50.121",
                  "group": 1,
                  "vlans": [
                    1
                  ],
                  "vcpu_total": 24,
                  "vcpu_allocated": 14,
                  "mem_total": 132768,
                  "mem_allocated": 9216,
                  "mem_reserved": 12038,
                  "vm_limit": 10,
                  "vm_created": 8,
                  "enable": true,
                  "desc": ""
                }
              ]
            }
        '''
        group_id = int(request.query_params.get('group_id', 0))
        vlan_id = int(request.query_params.get('vlan_id', 0))

        try:
            queryset = HostManager().filter_hosts_queryset(group_id=group_id, vlan_id=vlan_id)
        except ComputeError as e:
            return  Response(data={'code': 400, 'code_text': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        Defaults to using `self.serializer_class`.
        Custom serializer_class
        """
        if self.action in ['list', 'retrieve']:
            return serializers.HostSerializer
        return Serializer


class VlanViewSet(viewsets.GenericViewSet):
    '''
    vlan类视图
    '''
    permission_classes = [IsAuthenticated, ]
    pagination_class = LimitOffsetPagination
    queryset = Vlan.objects.all()

    # api docs
    schema = CustomAutoSchema(
        manual_fields={
        }
    )

    def list(self, request, *args, **kwargs):
        '''
        获取网段列表
        '''
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        Defaults to using `self.serializer_class`.
        Custom serializer_class
        """
        if self.action in ['list', 'retrieve']:
            return serializers.VlanSerializer
        return Serializer


class ImageViewSet(viewsets.GenericViewSet):
    '''
    镜像类视图
    '''
    permission_classes = [IsAuthenticated, ]
    pagination_class = LimitOffsetPagination
    queryset = Image.objects.all()

    # api docs
    schema = CustomAutoSchema(
        manual_fields={
            'list': [
                coreapi.Field(
                    name='center_id',
                    location='query',
                    required=False,
                    schema=coreschema.Integer(description='分中心id'),
                    description='所属分中心'
                )
            ]
        }
    )

    def list(self, request, *args, **kwargs):
        '''
        获取系统镜像列表
        '''
        center_id = int(request.query_params.get('center_id', 0))
        if center_id > 0:
            try:
                queryset = CenterManager().get_image_queryset_by_center(center_id)
            except Exception as e:
                return Response({'code': 400, 'code_text': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            queryset = self.get_queryset()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # def create(self, request, *args, **kwargs):
    #     pass
    #
    # def retrieve(self, request, *args, **kwargs):
    #     pass
    #
    # def destroy(self, request, *args, **kwargs):
    #     pass

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        Defaults to using `self.serializer_class`.
        Custom serializer_class
        """
        if self.action in ['list', 'retrieve']:
            return serializers.ImageSerializer
        return Serializer


class AuthTokenViewSet(ObtainAuthToken):
    '''
    get:
    获取当前用户的token，需要通过身份认证权限(如session认证)

        返回内容：
        {
            "token": {
                "key": "655e0bcc7216d0ccf7d2be7466f94fa241dc32cb",
                "user": "username",
                "created": "2018-12-10 14:04:01"
            }
        }

    put:
    刷新当前用户的token，旧token失效，需要通过身份认证权限

    post:
    身份验证并返回一个token，用于其他API验证身份

        令牌应包含在AuthorizationHTTP标头中。密钥应以字符串文字“Token”为前缀，空格分隔两个字符串。
        例如Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b；
        此外，可选Path参数,“new”，?new=true用于刷新生成一个新token；
    '''
    common_manual_fields = [
        coreapi.Field(
            name='version',
            required=True,
            location='path',
            schema=coreschema.String(description='API版本（v3, v4）')
        ),
    ]

    schema = CustomAutoSchema(
        manual_fields={
            'POST': common_manual_fields + [
                coreapi.Field(
                    name="username",
                    required=True,
                    location='form',
                    schema=coreschema.String(
                        title="Username",
                        description="Valid username for authentication",
                    ),
                ),
                coreapi.Field(
                    name="password",
                    required=True,
                    location='form',
                    schema=coreschema.String(
                        title="Password",
                        description="Valid password for authentication",
                    ),
                ),
                coreapi.Field(
                    name="new",
                    required=False,
                    location='query',
                    schema=coreschema.Boolean(description="为true时,生成一个新token"),
                ),
            ],
            'GET': common_manual_fields,
            'PUT': common_manual_fields,
        }
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            token, created = Token.objects.get_or_create(user=user)
            slr = serializers.AuthTokenDumpSerializer(token)
            return Response({'token': slr.data})
        return Response({'code': 403, 'code_text': '您没有访问权限'}, status=status.HTTP_403_FORBIDDEN)

    def put(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            token, created = Token.objects.get_or_create(user=user)
            if not created:
                token.delete()
                token.key = token.generate_key()
                token.save()
            slr = serializers.AuthTokenDumpSerializer(token)
            return Response({'token': slr.data})
        return Response({'code': 403, 'code_text': '您没有访问权限'}, status=status.HTTP_403_FORBIDDEN)

    def post(self, request, *args, **kwargs):
        new = request.query_params.get('new', None)
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        if new == 'true' and not created:
            token.delete()
            token.key = token.generate_key()
            token.save()

        slr = serializers.AuthTokenDumpSerializer(token)
        return Response({'token': slr.data})

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.request.method.upper() in ['POST']:
            return []
        return [IsAuthenticated()]

