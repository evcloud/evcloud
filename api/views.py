from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.serializers import Serializer
from rest_framework.decorators import action
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from drf_yasg.utils import swagger_auto_schema, no_body
from drf_yasg import openapi

from vms.manager import VmManager, VmAPI, VmError, FlavorManager
from novnc.manager import NovncTokenManager, NovncError
from compute.models import Center, Group, Host
from compute.managers import HostManager, CenterManager, GroupManager, ComputeError
from network.managers import VlanManager
from network.managers import MacIPManager
from image.managers import ImageManager
from vdisk.models import Vdisk
from vdisk.manager import VdiskManager,VdiskError
from device.manager import PCIDeviceManager, DeviceError
from . import serializers


def serializer_error_msg(errors, default=''):
    """
    获取一个错误信息

    :param errors: serializer.errors
    :param default:
    :return:
        str
    """
    msg = default
    try:
        if isinstance(errors, list):
            for err in errors:
                msg = str(err)
                break
        elif isinstance(errors, dict):
            for key in errors:
                val = errors[key]
                msg = f'{key}, {str(val[0])}'
                break
    except:
        pass

    return msg


def str_to_int_or_default(val, default):
    '''
    字符串转int，转换失败返回设置的默认值

    :param val: 待转化的字符串
    :param default: 转换失败返回的值
    :return:
        int     # success
        default # failed
    '''
    try:
        return int(val)
    except Exception:
        return default


class IsSuperUser(BasePermission):
    """
    Allows access only to super users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


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
              "image": "centos8",
              "disk": "4c0cdba7fe97405bac174baa03f3d036",
              "host": "10.100.50.121",
              "mac_ip": "10.107.50.252",
              "user": {
                "id": 3,
                "username": "test"
              },
              "create_time": "2020-03-06T14:46:27.149648+08:00"
            },
          ]
        }

    create:
        创建虚拟机

        vcpu和mem参数后续废弃，请使用flaver_id代替。

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
            "create_time": "2020-03-06T14:46:27.149648+08:00"
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

        获取虚拟机详细信息

        http code: 200, 请求成功：
        {
          "code": 200,
          "code_text": "获取虚拟机信息成功",
          "vm": {
            "uuid": "5b1f9a09b7224bdeb2ae12678ad0b1d4",
            "name": "5b1f9a09b7224bdeb2ae12678ad0b1d4",
            "vcpu": 2,
            "mem": 2048,        # MB
            "disk": "5b1f9a09b7224bdeb2ae12678ad0b1d4",
            "host": "10.100.50.121",
            "mac_ip": "10.107.50.253",
            "user": {
              "id": 1,
              "username": "shun"
            },
            "create_time": "2020-03-06T14:46:27.149648+08:00"
            "vdisks": [
              {
                "uuid": "063fc7830cce4b04a01a48572ea80198",
                "size": 6,      # GB
                "vm": {
                  "uuid": "c6c8f333bc9c426dad04a040ddd44b47",
                  "ipv4": "10.107.50.15"
                },
                "user": {
                  "id": 1,
                  "username": "shun"
                },
                "quota": {
                  "id": 1,
                  "name": "group1云硬盘存储池"
                },
                "create_time": "2020-03-06T14:46:27.149648+08:00"
                "attach_time": "2020-03-06T14:46:27.149648+08:00"
                "enable": true,
                "remarks": "",
                "group": {
                  "id": 1,
                  "name": "宿主机组1"
                }
              }
            ],
            "pci_devices": [
              {
                "id": 1,
                "type": {
                  "val": 1,
                  "name": "GPU"
                },
                "vm": {
                  "uuid": "c6c8f333bc9c426dad04a040ddd44b47",
                  "ipv4": "10.107.50.15"
                },
                "host": {
                  "id": 1,
                  "ipv4": "10.100.50.121"
                },
                "attach_time": "2020-03-06T14:46:27.149648+08:00"
                "remarks": ""
              }
            ]
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
    '''
    permission_classes = [IsAuthenticated,]
    pagination_class = LimitOffsetPagination
    lookup_field = 'uuid'
    lookup_value_regex = '[0-9a-z-]+'

    @swagger_auto_schema(
        operation_summary='虚拟机列表',
        manual_parameters=[
            openapi.Parameter(
                name='center_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='所属分中心id'
            ),
            openapi.Parameter(
                name='group_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='所属宿主机组id'
            ),
            openapi.Parameter(
                name='host_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='所属宿主机id'
            ),
            openapi.Parameter(
                name='user_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='所属用户id，当前为超级用户时此参数有效'
            ),
            openapi.Parameter(
                name='search',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description='关键字查询'
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        center_id = str_to_int_or_default(request.query_params.get('center_id', 0), default=0)
        group_id = str_to_int_or_default(request.query_params.get('group_id', 0), default=0)
        host_id = str_to_int_or_default(request.query_params.get('host_id', 0), default=0)
        user_id = str_to_int_or_default(request.query_params.get('user_id', 0), default=0)
        search = request.query_params.get('search', '')

        user = request.user
        manager = VmManager()
        try:
            if user.is_superuser: # 当前是超级用户，user_id查询参数有效
                self.queryset = manager.filter_vms_queryset(center_id=center_id, group_id=group_id, host_id=host_id,
                                                            search=search, user_id=user_id, all_no_filters=True)
            else:
                self.queryset = manager.filter_vms_queryset(center_id=center_id, group_id=group_id, host_id=host_id,
                                                    search=search, user_id=user.id)
        except VmError as e:
            return Response(data={'code': 400, 'code_text': '查询虚拟机时错误'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        data = {'results': serializer.data}
        return Response(data)

    @swagger_auto_schema(
        operation_summary='查询PCI设备可挂载的虚拟机',
        responses={
            200: ''
        }
    )
    @action(methods=['get'], detail=False, url_path=r'pci/(?P<pci_id>[0-9]+)', url_name='can_mount_pci')
    def can_mount_pci(self, request, *args, **kwargs):
        """
        查询PCI设备可挂载的虚拟机

            HTTP CODE 200:
            {
              "count": 1,
              "next": null,
              "previous": null,
              "results": [
                {
                  "uuid": "c6c8f333bc9c426dad04a040ddd44b47",
                  "name": "c6c8f333bc9c426dad04a040ddd44b47",
                  "vcpu": 2,
                  "mem": 1024,
                  "image": "centos8",
                  "disk": "c6c8f333bc9c426dad04a040ddd44b47",
                  "host": "10.100.50.121",
                  "mac_ip": "10.107.50.15",
                  "user": {
                    "id": 4,
                    "username": "869588058@qq.com"
                  },
                  "create_time": "2020-03-06T14:46:27.149648+08:00"
                }
              ]
            }
        """
        pci_id = str_to_int_or_default(kwargs.get('pci_id', 0), 0)
        if pci_id <= 0:
            return Response({'code': 400, 'code_text': '无效的PCI ID'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            dev = PCIDeviceManager().get_device_by_id(device_id=pci_id)
        except DeviceError as e:
            return Response({'code': 400, 'code_text': f'查询PCI设备错误，{str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        if not dev:
            return Response({'code': 404, 'code_text': 'PCI设备不存在'}, status=status.HTTP_404_NOT_FOUND)

        host = dev.host
        user = request.user
        mgr = VmManager()
        try:
            qs = mgr.get_vms_queryset_by_host(host)
            qs = qs.select_related('user', 'image', 'mac_ip', 'host')
            if not user.is_superuser:
                qs = qs.filter(user=user).all()
        except VmError as e:
            return Response({'code': 400, 'code_text': f'查询主机错误，{str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        data = {'results': serializer.data}
        return Response(data)

    @swagger_auto_schema(
        operation_summary='查询硬盘可挂载的虚拟机',
        responses={
            200: ''
        }
    )
    @action(methods=['get'], detail=False, url_path=r'vdisk/(?P<vdisk_uuid>[0-9a-z-]+)', url_name='can_mount_vdisk')
    def can_mount_vdisk(self, request, *args, **kwargs):
        """
        查询硬盘可挂载的虚拟机

            HTTP CODE 200:
            {
              "count": 1,
              "next": null,
              "previous": null,
              "results": [
                {
                  "uuid": "c6c8f333bc9c426dad04a040ddd44b47",
                  "name": "c6c8f333bc9c426dad04a040ddd44b47",
                  "vcpu": 2,
                  "mem": 1024,
                  "image": "centos8",
                  "disk": "c6c8f333bc9c426dad04a040ddd44b47",
                  "host": "10.100.50.121",
                  "mac_ip": "10.107.50.15",
                  "user": {
                    "id": 4,
                    "username": "869588058@qq.com"
                  },
                  "create_time": "2020-03-06T14:46:27.149648+08:00"
                }
              ]
            }
        """
        vdisk_uuid = kwargs.get('vdisk_uuid', '')
        if not vdisk_uuid:
            return Response({'code': 400, 'code_text': '无效的VDisk UUID'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            vdisk = VdiskManager().get_vdisk_by_uuid(uuid=vdisk_uuid, related_fields=('quota__group',))
        except DeviceError as e:
            return Response({'code': 400, 'code_text': f'查询硬盘错误，{str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        if not vdisk:
            return Response({'code': 404, 'code_text': '硬盘不存在'}, status=status.HTTP_404_NOT_FOUND)

        group = vdisk.quota.group
        user = request.user
        mgr = VmManager()
        try:
            queryset = mgr.get_vms_queryset_by_group(group)
            queryset = queryset.select_related('user', 'image', 'mac_ip', 'host').all()
            if not user.is_superuser:
                queryset = queryset.filter(user=user).all()
        except VmError as e:
            return Response({'code': 400, 'code_text': f'查询主机错误，{str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        data = {'results': serializer.data}
        return Response(data)

    @swagger_auto_schema(
        operation_summary='创建虚拟机',
        responses={
            201: ''
        }
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid(raise_exception=False):
            code_text = serializer_error_msg(errors=serializer.errors, default='参数验证有误')
            data = {
                'code': 400,
                'code_text': code_text,
                'data': serializer.data,
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        # 配置样式
        flavor_id = validated_data.get('flavor_id')
        if flavor_id:
            flavor = FlavorManager().get_flavor_by_id(flavor_id)
            if not flavor:
                data = {
                    'code': 404,
                    'code_text': '配置样式flavor不存在',
                    'data': serializer.data,
                }
                return Response(data, status=status.HTTP_404_NOT_FOUND)
            else:
                validated_data['vcpu'] = flavor.vcpus
                validated_data['mem'] = flavor.ram

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

    @swagger_auto_schema(
        operation_summary='获取虚拟机详细信息',
        responses={
            200: ''
        }
    )
    def retrieve(self, request, *args, **kwargs):
        vm_uuid = kwargs.get(self.lookup_field, '')
        try:
            vm = VmManager().get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=('image', 'mac_ip', 'host', 'user'))
        except VmError as e:
            return Response(data={'code': 500, 'code_text': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not vm:
            return Response(data={'code': 404, 'code_text': '虚拟机不存在'}, status=status.HTTP_404_NOT_FOUND)
        if not vm.user_has_perms(user=request.user):
            return Response(data={'code': 404, 'code_text': '当前用户没有权限访问此虚拟机'}, status=status.HTTP_404_NOT_FOUND)

        return Response(data={
            'code': 200,
            'code_text': '获取虚拟机信息成功',
            'vm': serializers.VmDetailSerializer(vm).data
        })

    @swagger_auto_schema(
        operation_summary='删除虚拟机',
        manual_parameters=[
            openapi.Parameter(
                name='force',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_BOOLEAN,
                required=False,
                description='true:强制删除'
            )
        ],
        responses={
            204: 'SUCCESS NO CONTENT'
        }
    )
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

    @swagger_auto_schema(
        operation_summary='修改虚拟机vcpu和内存大小',
        responses={
            200: '''
                {
                    "code": 200,
                    "code_text": "修改虚拟机成功"
                }
            '''
        }
    )
    def partial_update(self, request, *args, **kwargs):
        '''
        修改虚拟机vcpu和内存大小

            http code 200 修改成功：
            {
                "code": 200,
                "code_text": "修改虚拟机成功"
            }
            http code 400 修改失败：
            {
                "code": 400,
                "code_text": "xxx"
            }
        '''
        vm_uuid = kwargs.get(self.lookup_field, '')

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid(raise_exception=False):
            code_text = serializer_error_msg(serializer.errors, '参数验证有误')
            data = {
                'code': 400,
                'code_text': code_text,
                'data': serializer.data,
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        # 配置样式
        flavor_id = serializer.validated_data.get('flavor_id')
        flavor = FlavorManager().get_flavor_by_id(flavor_id)
        if not flavor:
            data = {
                'code': 404,
                'code_text': '配置样式flavor不存在',
                'data': serializer.data,
            }
            return Response(data, status=status.HTTP_404_NOT_FOUND)

        vcpu = flavor.vcpus
        mem = flavor.ram
        api = VmAPI()
        try:
            ok = api.edit_vm_vcpu_mem(user=request.user, vm_uuid=vm_uuid, mem=mem, vcpu=vcpu)
        except VmError as e:
            return Response(data={'code': 400, 'code_text': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if not ok:
            return Response(data={'code': 400, 'code_text': '修改虚拟机失败'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data={'code': 200, 'code_text': '修改虚拟机成功'})

    @swagger_auto_schema(
        operation_summary='操作虚拟机',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'op': openapi.Schema(
                    title='操作',
                    type=openapi.TYPE_STRING,
                    enum=['start', 'reboot', 'shutdown', 'poweroff', 'delete', 'delete_force'],
                    description="操作选项",
                )
            }
        ),
        responses={
            200: '''
            {
                'code': 200,
                'code_text': '操作虚拟机成功'
            }
            '''
        }
    )
    @action(methods=['patch'], url_path='operations', detail=True, url_name='vm-operations')
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

    @swagger_auto_schema(
        operation_summary='获取虚拟机当前运行状态',
        request_body=no_body,
        responses={
            200: '''
            {
              "code": 200,
              "code_text": "获取信息成功",
              "status": {
                "status_code": 5,
                "status_text": "shut off"
              }
            }
            '''
        }
    )
    @action(methods=['get'], url_path='status', detail=True, url_name='vm-status')
    def vm_status(self, request, *args, **kwargs):
        vm_uuid = kwargs.get(self.lookup_field, '')
        api = VmAPI()
        try:
            code, msg = api.get_vm_status(user=request.user, vm_uuid=vm_uuid)
        except VmError as e:
            return Response(data={'code': 400, 'code_text': f'获取虚拟机状态失败，{str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data={'code': 200, 'code_text': '获取虚拟机状态成功',
                              'status': {'status_code': code, 'status_text': msg}})

    @swagger_auto_schema(
        operation_summary='创建虚拟机vnc',
        request_body=no_body,
        responses={
            200: '''
            {
              "code": 200,
              "code_text": "创建虚拟机vnc成功",
              "vnc": {
                "id": "42bfe71e-6419-474a-bc99-9e519637797d",
                "url": "http://159.226.91.140:8000/novnc/?vncid=42bfe71e-6419-474a-bc99-9e519637797d"
              }
            }
            '''
        }
    )
    @action(methods=['post'], url_path='vnc', detail=True, url_name='vm-vnc')
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
            vm = VmManager().get_vm_by_uuid(vm_uuid=vm_uuid)
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

    @swagger_auto_schema(
        operation_summary='修改虚拟机备注信息',
        request_body=no_body,
        manual_parameters=[
            openapi.Parameter(
                name='remark',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=True,
                description='虚拟机备注信息'
            )
        ],
        responses={
            200: '''
            {
                'code': 200,
                'code_text': '修改虚拟机备注信息成功'
            }
            ''',
            400: '''
                {
                    'code': 400,
                    'code_text': 'xxx'
                }
                '''
        }
    )
    @action(methods=['patch'], url_path='remark', detail=True, url_name='vm-remark')
    def vm_remark(self, request, *args, **kwargs):
        '''
        修改虚拟机备注信息
        '''
        remark = request.query_params.get('remark', None)
        if remark is None:
            return Response(data={'code': 400, 'code_text': '参数有误，无效的备注信息'}, status=status.HTTP_400_BAD_REQUEST)

        vm_uuid = kwargs.get(self.lookup_field, '')
        api = VmAPI()
        try:
            api.modify_vm_remark(user=request.user, vm_uuid=vm_uuid, remark=remark)
        except VmError as e:
            return Response(data={'code': 400, 'code_text': f'修改虚拟机备注信息失败，{str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data={'code': 200, 'code_text': '修改虚拟机备注信息成功'})

    @swagger_auto_schema(
        operation_summary='创建虚拟机系统盘快照',
        request_body=no_body,
        manual_parameters=[
            openapi.Parameter(
                name='remark',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description='快照备注信息'
            )
        ],
        responses={
            201: '''
            {
              "code": 201,
              "code_text": "创建虚拟机系统快照成功",
              "snap": {
                "id": 45,
                "vm": {
                  "uuid": "598fb694a75c49c49c9574f9f3ea6174",
                  "ipv4": "10.107.50.2"
                },
                "snap": "598fb694a75c49c49c9574f9f3ea6174@20200121_073930",
                "create_time": "2020-03-06T14:46:27.149648+08:00",
                "remarks": "sss"
              }
            }
            ''',
            400: '''
            {
                'code': 400,
                'code_text': 'xxx'
            }
            '''
        }
    )
    @action(methods=['post'], url_path='snap', detail=True, url_name='vm-sys-snap')
    def vm_sys_snap(self, request, *args, **kwargs):
        '''
        创建虚拟机系统盘快照
        '''
        remark = request.query_params.get('remark', '')
        vm_uuid = kwargs.get(self.lookup_field, '')
        api = VmAPI()
        try:
            snap = api.create_vm_sys_snap(vm_uuid=vm_uuid, remarks=remark, user=request.user)
        except VmError as e:
            return Response(data={'code': 400, 'code_text': f'创建虚拟机系统快照失败，{str(e)}'},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(data={'code': 201, 'code_text': '创建虚拟机系统快照成功',
                              'snap': serializers.VmDiskSnapSerializer(snap).data}, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary='删除一个虚拟机系统快照',
        manual_parameters=[
            openapi.Parameter(
                name='id',
                in_=openapi.IN_PATH,
                type=openapi.TYPE_STRING,
                required=True,
                description='快照id'
            )
        ],
        responses={
            204: '''SUCCESS NO CONTENT''',
            400: '''
                {
                    'code': 400,
                    'code_text': 'xxx'
                }
            '''
        }
    )
    @action(methods=['delete'], url_path=r'snap/(?P<id>[0-9]+)', detail=False, url_name='delete-vm-snap')
    def delete_vm_snap(self, request, *args, **kwargs):
        '''
        删除一个虚拟机系统快照
        '''
        snap_id = str_to_int_or_default(kwargs.get('id', '0'), default=0)
        if snap_id <= 0:
            return Response(data={'code': 400, 'code_text': '无效的id参数'}, status=status.HTTP_400_BAD_REQUEST)

        api = VmManager()
        try:
            ok = api.delete_sys_disk_snap(snap_id=snap_id, user=request.user)
        except VmError as e:
            return Response(data={'code': 400, 'code_text': f'删除虚拟机系统快照失败，{str(e)}'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_summary='修改虚拟机快照备注信息',
        request_body=no_body,
        manual_parameters=[
            openapi.Parameter(
                name='id',
                in_=openapi.IN_PATH,
                type=openapi.TYPE_STRING,
                required=True,
                description='快照id'
            ),
            openapi.Parameter(
                name='remark',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=True,
                description='快照备注信息'
            )
        ],
        responses={
            200: '''
                {
                    'code': 200,
                    'code_text': '修改快照备注信息成功'
                }
            ''',
            400: '''
                {
                    'code': 400,
                    'code_text': 'xxx'
                }
            '''
        }
    )
    @action(methods=['patch'], url_path=r'snap/(?P<id>[0-9]+)/remark', detail=False, url_name='vm-snap-remark')
    def vm_snap_remark(self, request, *args, **kwargs):
        '''
        修改虚拟机快照备注信息
        '''
        remark = request.query_params.get('remark', None)
        if remark is None:
            return Response(data={'code': 400, 'code_text': '参数有误，无效的备注信息'}, status=status.HTTP_400_BAD_REQUEST)

        snap_id = str_to_int_or_default(kwargs.get('id', '0'), default=0)
        if snap_id <= 0:
            return Response(data={'code': 400, 'code_text': '无效的id参数'}, status=status.HTTP_400_BAD_REQUEST)

        api = VmManager()
        try:
            snap = api.modify_sys_snap_remarks(snap_id=snap_id, remarks=remark, user=request.user)
        except VmError as e:
            return Response(data={'code': 400, 'code_text': f'修改快照备注信息失败，{str(e)}'},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(data={'code': 200, 'code_text': '修改快照备注信息成功'})

    @swagger_auto_schema(
        operation_summary='虚拟机系统盘回滚到指定快照',
        request_body=no_body,
        responses={
            201: '''
            {
                'code': 201,
                'code_text': '回滚虚拟机成功'
            }
            ''',
            400: '''
            {
                'code': 400,
                'code_text': 'xxx'
            }
            '''
        }
    )
    @action(methods=['post'], url_path=r'rollback/(?P<snap_id>[0-9]+)', detail=True, url_name='vm-rollback-snap')
    def vm_rollback_snap(self, request, *args, **kwargs):
        '''
        虚拟机系统盘回滚到指定快照
        '''
        vm_uuid = kwargs.get(self.lookup_field, '')
        snap_id = str_to_int_or_default(kwargs.get('snap_id', '0'), default=0)
        if snap_id <= 0:
            return Response(data={'code': 400, 'code_text': '无效的id参数'}, status=status.HTTP_400_BAD_REQUEST)

        api = VmAPI()
        try:
            ok = api.vm_rollback_to_snap(vm_uuid=vm_uuid, snap_id=snap_id, user=request.user)
        except VmError as e:
            return Response(data={'code': 400, 'code_text': f'回滚虚拟机失败，{str(e)}'},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(data={'code': 201, 'code_text': '回滚虚拟机成功'}, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary='更换虚拟机系统',
        request_body=no_body,
        responses={
            201: '''
                {
                    'code': 201,
                    'code_text': '更换虚拟机系统成功'
                }
                ''',
            400: '''
                {
                    'code': 400,
                    'code_text': 'xxx'
                }
                '''
        }
    )
    @action(methods=['post'], url_path=r'reset/(?P<image_id>[0-9]+)', detail=True, url_name='vm-reset')
    def vm_reset(self, request, *args, **kwargs):
        """
        更换虚拟机系统
        """
        vm_uuid = kwargs.get(self.lookup_field, '')
        image_id = str_to_int_or_default(kwargs.get('image_id', '0'), default=0)
        if image_id <= 0:
            return Response(data={'code': 400, 'code_text': '无效的id参数'}, status=status.HTTP_400_BAD_REQUEST)

        api = VmAPI()
        try:
            vm = api.change_sys_disk(vm_uuid=vm_uuid, image_id=image_id, user=request.user)
        except VmError as e:
            return Response(data={'code': 400, 'code_text': f'更换虚拟机系统失败，{str(e)}'},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(data={'code': 201, 'code_text': '更换虚拟机系统成功'}, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary='迁移虚拟机到指定宿主机',
        request_body=no_body,
        responses={
            201: '''
                    {
                        'code': 201,
                        'code_text': '迁移虚拟机成功'
                    }
                    ''',
            400: '''
                    {
                        'code': 400,
                        'code_text': 'xxx'
                    }
                    '''
        }
    )
    @action(methods=['post'], url_path=r'migrate/(?P<host_id>[0-9]+)', detail=True, url_name='vm_migrate')
    def vm_migrate(self, request, *args, **kwargs):
        """
        迁移虚拟机到指定宿主机
        """
        vm_uuid = kwargs.get(self.lookup_field, '')
        host_id = str_to_int_or_default(kwargs.get('host_id', '0'), default=0)
        if host_id <= 0:
            return Response(data={'code': 400, 'code_text': '无效的host id参数'}, status=status.HTTP_400_BAD_REQUEST)

        api = VmAPI()
        try:
            vm = api.migrate_vm(vm_uuid=vm_uuid, host_id=host_id, user=request.user)
        except VmError as e:
            return Response(data={'code': 400, 'code_text': f'迁移虚拟机失败，{str(e)}'},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(data={'code': 201, 'code_text': '迁移虚拟机成功'}, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary='修改虚拟机登录密码',
        responses={
            200: '''
                {
                  "code": 200,
                  "code_text": "修改虚拟机登录密码成功",
                }
                '''
        }
    )
    @action(methods=['post'], url_path='setpassword', detail=True, url_name='vm-change-password')
    def vm_change_password(self, request, *args, **kwargs):
        """
        创建虚拟机vnc

            >> http code 200:
            {
              "code": 200,
              "code_text": "修改虚拟机登录密码成功",
            }
        """
        vm_uuid = kwargs.get(self.lookup_field, '')

        serializer = serializers.VmChangePasswordSerializer(data=request.data)
        if not serializer.is_valid(raise_exception=False):
            msg = serializer_error_msg(serializer.errors, 'username或password无效')
            return Response(data={'code': 400, 'code_text': msg}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        username = data.get('username')
        password = data.get('password')
        
        try:
            vm = VmAPI().vm_change_password(vm_uuid=vm_uuid, user=request.user, username=username, password=password)
        except VmError as e:
            return Response(data={'code': 500, 'code_text': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(data={'code': 200, 'code_text': '修改虚拟机登录密码成功'})

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        Defaults to using `self.serializer_class`.
        Custom serializer_class
        """
        if self.action in ['list', 'retrieve', 'can_mount_pci', 'can_mount_vdisk']:
            return serializers.VmSerializer
        elif self.action == 'create':
            return serializers.VmCreateSerializer
        elif self.action == 'partial_update':
            return serializers.VmPatchSerializer
        elif self.action == 'vm_change_password':
            return serializers.VmChangePasswordSerializer
        return Serializer


class CenterViewSet(viewsets.GenericViewSet):
    '''
    分中心类视图
    '''
    permission_classes = [IsAuthenticated, ]
    pagination_class = LimitOffsetPagination
    queryset = Center.objects.all()

    def list(self, request, *args, **kwargs):
        '''
        获取分中心列表

            获取分中心列表信息

            http code 200:
            {
              "count": 1,
              "next": null,
              "previous": null,
              "results": [
                {
                  "id": 1,
                  "name": "怀柔分中心",
                  "location": "怀柔",
                  "desc": "xxx"
                }
              ]
            }
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

    @swagger_auto_schema(
        operation_summary='获取宿主机组列表',
        manual_parameters=[
            openapi.Parameter(
                name='center_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='所属分中心id'
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        '''
        获取宿主机组列表

            获取宿主机组列表信息

            http code 200:
            {
              "count": 2,
              "next": null,
              "previous": null,
              "results": [
                {
                  "id": 1,
                  "name": "宿主机组1",
                  "center": 1,
                  "desc": "xxx"
                },
              ]
            }
            http code 400:
            {
              "code": 400,
              "code_text": "xxx"
            }
        '''
        center_id = str_to_int_or_default(request.query_params.get('center_id', 0), 0)
        if center_id < 0:
            return Response(data={'code': 400, 'code_text': 'center_id参数无效'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        manager = CenterManager()
        try:
            if center_id > 0:
                if user.is_superuser:
                    queryset = manager.get_group_queryset_by_center(center_id)
                else:
                    queryset = manager.get_user_group_queryset_by_center(center_or_id=center_id, user=user)
            else:
                if user.is_superuser:
                    queryset = self.get_queryset()
                else:
                    queryset = manager.get_user_group_queryset(user)
        except ComputeError as e:
            return Response(data={'code': 400, 'code_text': str(e)}, status=status.HTTP_400_BAD_REQUEST)

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

    @swagger_auto_schema(
        operation_summary='获取宿主机列表',
        manual_parameters=[
            openapi.Parameter(
                name='group_id', in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='宿主机组id'
            ),
            openapi.Parameter(
                name='vlan_id', in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="子网网段id",
                required=False
            )
        ]
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

    @swagger_auto_schema(
        operation_summary='获取网段列表',
        manual_parameters=[
            openapi.Parameter(
                name='center_id', in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='分中心id'
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        '''
        获取网段列表
        '''
        center_id = request.query_params.get('center_id', None)
        if center_id is not None:
            center_id = str_to_int_or_default(center_id, 0)
            if center_id <= 0:
                return Response(data={'code': 400, 'code_text': 'query参数center_id无效'}, status=status.HTTP_400_BAD_REQUEST)
            queryset = VlanManager().get_center_vlan_queryset(center=center_id)
        else:
            queryset = VlanManager().get_vlan_queryset()

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

    @swagger_auto_schema(
        operation_summary='获取系统镜像列表',
        manual_parameters=[
            openapi.Parameter(
                name='center_id', in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='所属分中心id'
            ),
            openapi.Parameter(
                name='tag', in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="镜像标签",
                required=False
            ),
            openapi.Parameter(
                name='sys_type', in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='系统类型'
            ),
            openapi.Parameter(
                name='search', in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="关键字查询",
                required=False
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        '''
        获取系统镜像列表

            镜像标签: [
                [1, "基础镜像" ],
                [2, "用户镜像"]
            ]
            系统类型: [
                [1,"Windows"],
                [2,"Linux"],
                [3,"Unix"],
                [4,"MacOS"],
                [5,"Android"],
                [6,"其他"]
            ]

            http code 200:
            {
              "count": 2,
              "next": null,
              "previous": null,
              "results": [
                {
                  "id": 1,
                  "name": "centos8",
                  "version": "64bit",
                  "sys_type": {
                    "id": 2,
                    "name": "Linux"
                  },
                  "tag": {
                    "id": 0,
                    "name": "基础镜像"
                  },
                  "enable": true,
                  "create_time": "2020-03-06T14:46:27.149648+08:00",
                  "desc": "centos8"
                }
              ]
            }
        '''
        center_id = str_to_int_or_default(request.query_params.get('center_id', 0), 0)
        tag = str_to_int_or_default(request.query_params.get('tag', 0), 0)
        sys_type = str_to_int_or_default(request.query_params.get('sys_type', 0), 0)
        search = request.query_params.get('sys_type', '')

        try:
            queryset = ImageManager().filter_image_queryset(center_id=center_id, sys_type=sys_type, tag=tag,
                                                            search=search, all_no_filters=True)
        except Exception as e:
            return Response({'code': 400, 'code_text': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({'results': serializer.data})

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
    获取当前用户的token

        获取当前用户的token，需要通过身份认证权限(如session认证)

        code 200 返回内容：
        {
            "token": {
                "key": "655e0bcc7216d0ccf7d2be7466f94fa241dc32cb",
                "user": "username",
                "created": "2020-03-06T14:46:27.149648+08:00"
            }
        }

    post:
    身份验证并返回一个token，用于其他API验证身份

        令牌应包含在AuthorizationHTTP标头中。密钥应以字符串文字“Token”为前缀，空格分隔两个字符串。
        例如Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b；
        此外，可选Path参数,“new”，?new=true用于刷新生成一个新token；
    '''

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            token, created = Token.objects.get_or_create(user=user)
            slr = serializers.AuthTokenDumpSerializer(token)
            return Response({'token': slr.data})
        return Response({'code': 403, 'code_text': '您没有访问权限'}, status=status.HTTP_403_FORBIDDEN)

    @swagger_auto_schema(
        operation_summary='刷新当前用户的token',
        responses={
            200:'''
            {
                "token": {
                    "key": "655e0bcc7216d0ccf7d2be7466f94fa241dc32cb",
                    "user": "username",
                    "created": "2020-03-06T14:46:27.149648+08:00"
                }
            }
            '''
        }
    )
    def put(self, request, *args, **kwargs):
        '''
        刷新当前用户的token，旧token失效，需要通过身份认证权限
        '''
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

    @swagger_auto_schema(
        operation_summary='身份验证获取一个token',
        request_body=AuthTokenSerializer(),
        manual_parameters=[
            openapi.Parameter(
                name='new',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_BOOLEAN,
                required=False,
                description='为true时,生成一个新token'
            )
        ],
        responses={
            200: '''
                {
                    "token": {
                        "key": "655e0bcc7216d0ccf7d2be7466f94fa241dc32cb",
                        "user": "username",
                        "created": "2020-03-06T14:46:27.149648+08:00"
                    }
                }
            '''
        }
    )
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


class JWTObtainPairView(TokenObtainPairView):
    '''
    JWT登录认证视图
    '''

    @swagger_auto_schema(
        operation_summary='登录认证，获取JWT',
        responses={
            200: '''
                {
                  "refresh": "xxx",     # refresh JWT, 此JWT通过刷新API可以获取新的access JWT
                  "access": "xxx"       # access JWT, 用于身份认证，如 'Authorization Bearer accessJWT'
                }
            '''
        }
    )
    def post(self, request, *args, **kwargs):
        '''
        登录认证，获取JWT

            http 200:
            {
              "refresh": "xxx",     # refresh JWT, 此JWT通过刷新API可以获取新的access JWT
              "access": "xxx"       # access JWT, 用于身份认证，如 'Authorization Bearer accessJWT'
            }
            http 401:
            {
              "detail": "No active account found with the given credentials"
            }
        '''
        return super().post(request, args, kwargs)


class JWTRefreshView(TokenRefreshView):
    '''
    Refresh JWT视图
    '''
    @swagger_auto_schema(
        operation_summary='刷新access JWT',
        responses={
            200: '''
                {
                  "access": "xxx"
                }
            '''
        }
    )
    def post(self, request, *args, **kwargs):
        '''
        通过refresh JWT获取新的access JWT

            http 200:
            {
              "access": "xxx"
            }
            http 401:
            {
              "detail": "Token is invalid or expired",
              "code": "token_not_valid"
            }
        '''
        return super().post(request, args, kwargs)


class JWTVerifyView(TokenVerifyView):
    '''
    校验access JWT视图
    '''

    @swagger_auto_schema(
        operation_summary='校验access JWT是否有效',
        responses={
            200: '''{ }'''
        }
    )
    def post(self, request, *args, **kwargs):
        '''
        校验access JWT是否有效

            http 200:
            {
            }
            http 401:
            {
              "detail": "Token is invalid or expired",
              "code": "token_not_valid"
            }
        '''
        return super().post(request, args, kwargs)


class VDiskViewSet(viewsets.GenericViewSet):
    '''
    虚拟硬盘类视图
    '''
    permission_classes = [IsAuthenticated, ]
    pagination_class = LimitOffsetPagination
    lookup_field = 'uuid'
    lookup_value_regex = '[0-9a-z-]+'
    queryset = Vdisk.objects.all()

    @swagger_auto_schema(
        operation_summary='获取云硬盘列表',
        manual_parameters=[
            openapi.Parameter(
                name='center_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='所属分中心id'
            ),
            openapi.Parameter(
                name='group_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='所属机组id'
            ),
            openapi.Parameter(
                name='quota_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='所属硬盘存储池id'
            ),
            openapi.Parameter(
                name='user_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='所属用户id，当前为超级用户时此参数有效'
            ),
            openapi.Parameter(
                name='search',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description='查询关键字'
            ),
            openapi.Parameter(
                name='mounted',
                in_=openapi.IN_QUERY,
                required=False,
                type=openapi.TYPE_BOOLEAN,
                description='是否挂载查询条件，true=已挂载；false=未挂载'
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        '''
        获取云硬盘列表

            http code 200:
            {
              "count": 1,
              "next": null,
              "previous": null,
              "results": [
                {
                  "uuid": "77a076b56220448f84700df51405e7df",
                  "size": 11,
                  "vm": {
                    "uuid": "c58125f6916b4028864b46c7c0b02d99",
                    "ipv4": "10.107.50.252"
                  },
                  "user": {
                    "id": 1,
                    "username": "shun"
                  },
                  "quota": {
                    "id": 1,
                    "name": "group1云硬盘存储池"
                  },
                  "create_time": "2020-03-06T14:46:27.149648+08:00",
                  "attach_time": "2020-03-06T14:46:27.149648+08:00",
                  "enable": true,
                  "remarks": "test3",
                  "group": {
                    "id": 1,
                    "name": "宿主机组1"
                  }
                }
              ]
            }
        '''
        center_id = int(request.query_params.get('center_id', 0))
        group_id = int(request.query_params.get('group_id', 0))
        quota_id = int(request.query_params.get('quota_id', 0))
        user_id = int(request.query_params.get('user_id', 0))
        search = request.query_params.get('search', '')
        mounted = request.query_params.get('mounted', '')

        user = request.user
        manager = VdiskManager()
        try:
            if user.is_superuser: # 当前是超级用户，user_id查询参数有效
                queryset = manager.filter_vdisk_queryset(center_id=center_id, group_id=group_id, quota_id=quota_id,
                                                              search=search, user_id=user_id, all_no_filters=True)
            else:
                queryset = manager.filter_vdisk_queryset(center_id=center_id, group_id=group_id, quota_id=quota_id,
                                                              search=search, user_id=user.id)
        except VdiskError as e:
            return Response(data={'code': 400, 'code_text': f'查询云硬盘时错误, {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        if mounted == 'true':
            queryset = queryset.filter(vm__isnull=False).all()
        elif mounted == 'false':
            queryset = queryset.filter(vm__isnull=True).all()

        try:
            page = self.paginate_queryset(queryset)
        except Exception as e:
            return Response(data={'code': 400, 'code_text': f'查询云硬盘时错误, {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            data = {'code': 200, 'disks': serializer.data, }
        return Response(data)

    @swagger_auto_schema(
        operation_summary='查询虚拟机可挂载的云硬盘',
        responses={
            200: ''''''
        }
    )
    @action(methods=['get'], detail=False, url_path=r'vm/(?P<vm_uuid>[0-9a-z-]+)', url_name='vm_can_mount')
    def vm_can_mount(self, request, *args, **kwargs):
        """
        查询虚拟机可挂载的云硬盘

            HTTP CODE 200:
            {
              "count": 1,
              "next": null,
              "previous": null,
              "results": [
                {
                  "uuid": "6111402f379b444092218101c72016c4",
                  "size": 10,
                  "vm": {                                          # 已挂载于主机；未挂载时为 null
                    "uuid": "c6c8f333bc9c426dad04a040ddd44b47",
                    "ipv4": "10.107.50.15"
                  },
                  "user": {
                    "id": 4,
                    "username": "869588058@qq.com"
                  },
                  "quota": {
                    "id": 1,
                    "name": "group1云硬盘存储池"
                  },
                  "create_time": "2020-03-09T16:36:53.717507+08:00",
                  "attach_time": "2020-03-12T16:02:00.738921+08:00",    # 挂载时间；未挂载时为 null
                  "enable": true,
                  "remarks": "",
                  "group": {
                    "id": 1,
                    "name": "宿主机组1"
                  }
                }
              ]
            }
        """
        vm_uuid = kwargs.get('vm_uuid', '')

        mgr = VmManager()
        try:
            vm = mgr.get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=('host', 'host__group', 'image'))
        except VmError as e:
            return Response({'code': 400, 'code_text': f'查询云主机错误，{str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        if not vm:
            return Response({'code': 404, 'code_text': '云主机不存在'}, status=status.HTTP_404_NOT_FOUND)

        group = vm.host.group
        user = request.user

        disk_manager = VdiskManager()
        related_fields = ('user', 'quota', 'quota__group')
        try:
            if user.is_superuser:
                queryset = disk_manager.filter_vdisk_queryset(group_id=group.id, related_fields=related_fields)
            else:
                queryset = disk_manager.filter_vdisk_queryset(group_id=group.id, user_id=user.id, related_fields=related_fields)
        except VdiskError as e:
            return Response({'code': 400, 'code_text': f'查询硬盘列表时错误，{str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        except Exception as e:
            return Response(data={'code': 400, 'code_text': f'查询云硬盘时错误, {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary='创建云硬盘',
        responses={
            201: ''''''
        }
    )
    def create(self, request, *args, **kwargs):
        '''
        创建云硬盘

            http code 201 创建成功:
            {
              "code": 201,
              "code_text": "创建成功",
              "disk": {
                "uuid": "972e015b3b4c491ca36b414dd517fdf0",
                "size": 2,
                "vm": null,
                "user": 1,
                "quota": 1,
                "create_time": "2020-03-06T14:46:27.149648+08:00",
                "attach_time": null,
                "enable": true,
                "remarks": "test2"
              }
            http code 200 失败：
            {
              "code": 200,
              "code_text": "创建失败，xxx",
            }

            http code 400 请求无效：
            {
              "code": 400,
              "code_text": "xxx",
              "data":{ }            # 请求时提交的数据
            }
        '''
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid(raise_exception=False):
            code_text = '参数验证有误'
            try:
                for name, err_list in serializer.errors.items():
                    if name == 'code_text':
                        code_text = err_list[0]
                    else:
                        code_text = f'"{name}" {err_list[0]}'
                    break
            except:
                pass

            data = {
                'code': 400,
                'code_text': code_text,
                'data': serializer.data,
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        size = data.get('size')
        group_id = data.get('group_id', None)
        quota_id = data.get('quota_id', None)
        remarks = data.get('remarks', '')

        manager = VdiskManager()
        try:
            disk = manager.create_vdisk(size=size, user=request.user, group=group_id, quota=quota_id, remarks=remarks)
        except VdiskError as e:
            return Response(data={'code': 200, 'code_text': str(e)}, status=status.HTTP_200_OK)

        data = {
            'code': 201,
            'code_text': '创建成功',
            'disk': serializers.VdiskSerializer(instance=disk).data,
        }
        return Response(data=data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        '''
        获取硬盘详细数据

            获取硬盘详细数据

            http code 200:
            {
              "code": 200,
              "code_text": "获取云硬盘信息成功",
              "vm": {
                "uuid": "296beb3413724456911077321a4247f9",
                "size": 1,
                "vm": null,
                "user": {
                  "id": 1,
                  "username": "shun"
                },
                "quota": {
                  "id": 1,
                  "name": "group1云硬盘存储池",
                  "pool": {
                    "id": 1,
                    "name": "vm1"
                  },
                  "ceph": {
                    "id": 1,
                    "name": "对象存储集群"
                  },
                  "group": {
                    "id": 1,
                    "name": "宿主机组1"
                  }
                },
                "create_time": "2020-03-06T14:46:27.149648+08:00",
                "attach_time": null,
                "enable": true,
                "remarks": "test"
              }
            }
        '''
        disk_uuid = kwargs.get(self.lookup_field, '')
        try:
            disk = VdiskManager().get_vdisk_by_uuid(uuid=disk_uuid)
        except VdiskError as e:
            return  Response(data={'code': 500, 'code_text': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not disk:
            return Response(data={'code': 404, 'code_text': '云硬盘不存在'}, status=status.HTTP_404_NOT_FOUND)
        if not disk.user_has_perms(user=request.user):
            return Response(data={'code': 404, 'code_text': '当前用户没有权限访问此云硬盘'}, status=status.HTTP_404_NOT_FOUND)

        return Response(data={
            'code': 200,
            'code_text': '获取云硬盘信息成功',
            'vm': self.get_serializer(disk).data
        })

    def destroy(self, request, *args, **kwargs):
        '''
        销毁硬盘

            销毁硬盘

            http code 204: 销毁成功
            http code 400,403, 404: 销毁失败
            {
                "code": 4xx,
                "code_text": "xxx"
            }
        '''
        disk_uuid = kwargs.get(self.lookup_field, '')
        api = VdiskManager()
        try:
            vdisk = api.get_vdisk_by_uuid(uuid=disk_uuid)
        except VdiskError as e:
            return Response(data={'code': 400, 'code_text': f'查询硬盘时错误，{str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        if vdisk is None:
            return Response(data={'code': 404, 'code_text': '硬盘不存在'}, status=status.HTTP_404_NOT_FOUND)

        if not vdisk.user_has_perms(user=request.user):
            return Response(data={'code': 403, 'code_text': '当前用户没有权限访问此硬盘'}, status=status.HTTP_403_FORBIDDEN)

        if vdisk.is_mounted:
            return Response(data={'code': 400, 'code_text': '硬盘已被挂载使用，请先卸载后再销毁'}, status=status.HTTP_400_BAD_REQUEST)

        if not vdisk.soft_delete():
            return Response(data={'code': 400, 'code_text': '销毁硬盘失败，数据库错误'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_summary='挂载硬盘',
        request_body=no_body,
        manual_parameters=[
            openapi.Parameter(
                name='vm_uuid',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=True,
                description='要挂载的虚拟机uuid'
            )
        ],
        responses={
            200: '''
                {
                    "code": 200,
                    "code_text": "挂载硬盘成功"
                }
            '''
        }
    )
    @action(methods=['patch'], url_path='mount', detail=True, url_name='disk-mount')
    def disk_mount(self, request, *args, **kwargs):
        '''
        挂载硬盘

            http code 200:
            {
                "code": 200,
                "code_text": "挂载硬盘成功"
            }
            http code 400:
            {
                "code": 400,
                "code_text": "挂载硬盘失败，xxx"
            }
        '''
        disk_uuid = kwargs.get(self.lookup_field, '')
        vm_uuid = request.query_params.get('vm_uuid', '')
        api = VmAPI()
        try:
            disk = api.mount_disk(user=request.user, vm_uuid=vm_uuid, vdisk_uuid=disk_uuid)
        except VmError as e:
            return Response(data={'code': 400, 'code_text': f'挂载硬盘失败，{str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data={'code': 200, 'code_text': '挂载硬盘成功'})

    @swagger_auto_schema(
        operation_summary='卸载硬盘',
        request_body=no_body,
        responses={
            200: '''
                {
                    "code": 200,
                    "code_text": "卸载硬盘成功"
                }
            '''
        }
    )
    @action(methods=['patch'], url_path='umount', detail=True, url_name='disk-umount')
    def disk_umount(self, request, *args, **kwargs):
        '''
        卸载硬盘

            http code 200:
            {
                "code": 200,
                "code_text": "卸载硬盘成功"
            }
            http code 400:
            {
                "code": 400,
                "code_text": "卸载硬盘失败，xxx"
            }
        '''
        disk_uuid = kwargs.get(self.lookup_field, '')
        api = VmAPI()
        try:
            disk = api.umount_disk(user=request.user, vdisk_uuid=disk_uuid)
        except VmError as e:
            return Response(data={'code': 400, 'code_text': f'卸载硬盘失败，{str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data={'code': 200, 'code_text': '卸载硬盘成功'})

    @swagger_auto_schema(
        operation_summary='修改云硬盘备注信息',
        request_body=no_body,
        manual_parameters=[
            openapi.Parameter(
                name='remark',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=True,
                description='新的备注信息'
            )
        ],
        responses={
            200: '''
                {
                    "code": 200,
                    "code_text": "修改硬盘备注信息成功"
                }
            ''',
            400: '''
                    {
                        "code": 400,
                        "code_text": "xxx"
                    }
                '''
        }
    )
    @action(methods=['patch'], url_path='remark', detail=True, url_name='disk-remark')
    def disk_remark(self, request, *args, **kwargs):
        '''
        修改云硬盘备注信息
        '''
        remark = request.query_params.get('remark', None)
        if remark is None:
            return Response(data={'code': 400, 'code_text': '参数有误，未提交remark参数'}, status=status.HTTP_400_BAD_REQUEST)

        vm_uuid = kwargs.get(self.lookup_field, '')
        api = VdiskManager()
        try:
            disk = api.modify_vdisk_remarks(user=request.user, uuid=vm_uuid, remarks=remark)
        except api.VdiskError as e:
            return Response(data={'code': 400, 'code_text': f'修改硬盘备注信息失败，{str(e)}'},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(data={'code': 200, 'code_text': '修改硬盘备注信息成功'})

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        Defaults to using `self.serializer_class`.
        Custom serializer_class
        """
        if self.action in ['list', 'vm_can_mount']:
            return serializers.VdiskSerializer
        elif self.action == 'retrieve':
            return serializers.VdiskDetailSerializer
        elif self.action == 'create':
            return serializers.VdiskCreateSerializer
        return Serializer


class QuotaViewSet(viewsets.GenericViewSet):
    '''
    硬盘存储池配额类视图
    '''
    permission_classes = [IsAuthenticated, ]
    pagination_class = LimitOffsetPagination

    @swagger_auto_schema(
        operation_summary='获取硬盘储存池配额列表',
        manual_parameters=[
            openapi.Parameter(
                name='group_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='筛选条件，所属宿主机组id'
            )
        ],
    )
    def list(self, request, *args, **kwargs):
        '''
        获取硬盘储存池配额列表

            http code 200:
            {
              "count": 1,
              "next": null,
              "previous": null,
              "results": [
                {
                  "id": 1,
                  "name": "group1云硬盘存储池",
                  "pool": {
                    "id": 1,
                    "name": "vm1"
                  },
                  "ceph": {
                    "id": 1,
                    "name": "对象存储集群"
                  },
                  "group": {
                    "id": 1,
                    "name": "宿主机组1"
                  }
                },
                "total": 100000,    # 总容量
                "size_used": 30,    # 已用容量
                "max_vdisk": 200    # 硬盘最大容量上限
              ]
            }
        '''
        group_id = int(request.query_params.get('group_id', 0))
        manager = VdiskManager()

        if group_id > 0:
            queryset = manager.get_quota_queryset_by_group(group=group_id)
        else:
            queryset = manager.get_quota_queryset()
            queryset = queryset.select_related('cephpool', 'cephpool__ceph', 'group').all()
        try:
            page = self.paginate_queryset(queryset)
        except Exception as e:
            return  Response(data={'code': 400, 'code_text': str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
            return serializers.QuotaListSerializer
        return Serializer


class StatCenterViewSet(viewsets.GenericViewSet):
    '''
    资源统计类视图
    '''
    permission_classes = [IsAuthenticated, IsSuperUser]
    pagination_class = None
    lookup_field = 'id'

    @swagger_auto_schema(
        operation_summary='获取所有资源统计信息',
        responses={
            200: ''
        }
    )
    def list(self, request, *args, **kwargs):
        '''
        获取所有资源统计信息列表

            http code 200:
            {
              "code": 200,
              "code_text": "get ok",
              "centers": [
                {
                  "id": 1,
                  "name": "怀柔分中心",
                  "mem_total": 165536,
                  "mem_allocated": 15360,
                  "mem_reserved": 2038,
                  "vcpu_total": 54,
                  "vcpu_allocated": 24,
                  "vm_created": 6
                }
              ],
              "groups": [
                {
                  "id": 1,
                  "name": "宿主机组1",
                  "center__name": "怀柔分中心",
                  "mem_total": 132768,
                  "mem_allocated": 15360,
                  "mem_reserved": 2038,
                  "vcpu_total": 24,
                  "vcpu_allocated": 24,
                  "vm_created": 6
                }
              ],
              "hosts": [
                {
                  "id": 1,
                  "ipv4": "10.100.50.121",
                  "group__name": "宿主机组1",
                  "mem_total": 132768,
                  "mem_allocated": 15360,
                  "mem_reserved": 2038,
                  "vcpu_total": 24,
                  "vcpu_allocated": 24,
                  "vm_created": 6
                }
              ]
            }
        '''
        centers = CenterManager().get_stat_center_queryset().values('id', 'name', 'mem_total', 'mem_allocated',
                                         'mem_reserved', 'vcpu_total', 'vcpu_allocated', 'vm_created')
        groups = GroupManager().get_stat_group_queryset().values('id', 'name', 'center__name', 'mem_total',
                                        'mem_allocated', 'mem_reserved', 'vcpu_total', 'vcpu_allocated', 'vm_created')
        hosts = Host.objects.select_related('group').values('id', 'ipv4', 'group__name', 'mem_total', 'mem_allocated',
                                            'mem_reserved', 'vcpu_total', 'vcpu_allocated', 'vm_created').all()
        return Response(data={'code': 200, 'code_text': 'get ok', 'centers': centers, 'groups': groups, 'hosts': hosts})

    @swagger_auto_schema(
        operation_summary='获取一个分中心的资源统计信息',
        responses={
            200: ''
        }
    )
    @action(methods=['get'], detail=True, url_path='center', url_name='center-stat')
    def center_stat(self, request, *args, **kwargs):
        '''
        获取一个分中心的资源统计信息列表

            http code 200:
            {
              "code": 200,
              "code_text": "get ok",
              "center": {
                  "id": 1,
                  "name": "怀柔分中心",
                  "mem_total": 165536,
                  "mem_allocated": 15360,
                  "mem_reserved": 2038,
                  "vcpu_total": 54,
                  "vcpu_allocated": 24,
                  "vm_created": 6
                },
              "groups": [
                {
                  "id": 1,
                  "name": "宿主机组1",
                  "center__name": "怀柔分中心",
                  "mem_total": 132768,
                  "mem_allocated": 15360,
                  "mem_reserved": 2038,
                  "vcpu_total": 24,
                  "vcpu_allocated": 24,
                  "vm_created": 6
                }
              ]
            }
        '''
        c_id = str_to_int_or_default(kwargs.get(self.lookup_field, 0), 0)
        if c_id > 0:
            center = CenterManager().get_stat_center_queryset(filters={'id': c_id}).values('id', 'name', 'mem_total',
                            'mem_allocated','mem_reserved', 'vcpu_total', 'vcpu_allocated', 'vm_created').first()
        else:
            center = None
        if not center:
            return Response({'code': 200, 'code_text': '分中心不存在'}, status=status.HTTP_400_BAD_REQUEST)

        groups = GroupManager().get_stat_group_queryset(filters={'center': c_id}).values('id', 'name', 'center__name',
                             'mem_total', 'mem_allocated', 'mem_reserved', 'vcpu_total', 'vcpu_allocated', 'vm_created')
        return Response(data={'code': 200, 'code_text': 'get ok', 'center': center, 'groups': groups})

    @swagger_auto_schema(
        operation_summary='获取一个机组的资源统计信息',
        responses={
            200: ''
        }
    )
    @action(methods=['get'], detail=True, url_path='group', url_name='group-stat')
    def group_stat(self, request, *args, **kwargs):
        '''
        获取一个机组的资源统计信息列表

            http code 200:
            {
              "code": 200,
              "code_text": "get ok",
              "group": {
                  "id": 1,
                  "name": "宿主机组1",
                  "center__name": "怀柔分中心",
                  "mem_total": 132768,
                  "mem_allocated": 15360,
                  "mem_reserved": 2038,
                  "vcpu_total": 24,
                  "vcpu_allocated": 24,
                  "vm_created": 6
              },
              "hosts": [
                {
                  "id": 1,
                  "ipv4": "10.100.50.121",
                  "group__name": "宿主机组1",
                  "mem_total": 132768,
                  "mem_allocated": 15360,
                  "mem_reserved": 2038,
                  "vcpu_total": 24,
                  "vcpu_allocated": 24,
                  "vm_created": 6
                }
              ]
            }
        '''
        g_id = str_to_int_or_default(kwargs.get(self.lookup_field, 0), 0)
        if g_id > 0:
            group = GroupManager().get_stat_group_queryset(filters={'id': g_id}).values('id', 'name', 'center__name',
                    'mem_total', 'mem_allocated', 'mem_reserved', 'vcpu_total','vcpu_allocated', 'vm_created').first()
        else:
            group = None
        if not group:
            return Response({'code': 200, 'code_text': '机组不存在'}, status=status.HTTP_400_BAD_REQUEST)

        hosts = Host.objects.select_related('group').filter(group=g_id).values('id', 'ipv4', 'group__name', 'mem_total',
                        'mem_allocated', 'mem_reserved', 'vcpu_total', 'vcpu_allocated', 'vm_created').all()
        return Response(data={'code': 200, 'code_text': 'get ok', 'group': group, 'hosts': hosts})

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        Defaults to using `self.serializer_class`.
        Custom serializer_class
        """
        return Serializer


class PCIDeviceViewSet(viewsets.GenericViewSet):
    '''
    PCI设备类视图
    '''
    permission_classes = [IsAuthenticated, ]
    pagination_class = LimitOffsetPagination

    @swagger_auto_schema(
        operation_summary='获取PCI设备列表',
        manual_parameters=[
            openapi.Parameter(
                name='center_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='筛选条件，所属分中心id'
            ),
            openapi.Parameter(
                name='group_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='筛选条件，所属宿主机组id'
            ),
            openapi.Parameter(
                name='host_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='筛选条件，所属宿主机id'
            ),
            openapi.Parameter(
                name='type',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='筛选条件，设备类型'
            ),
            openapi.Parameter(
                name='search',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description='筛选条件，关键字'
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        '''
        获取PCI设备列表

            http code 200:
            {
                "count": 1,
                "next": null,
                "previous": null,
                "results": [
                {
                  "id": 1,
                  "type": {
                    "val": 1,
                    "name": "GPU"
                  },
                  "vm": null,
                  "host": {
                    "id": 1,
                    "ipv4": "10.100.50.121"
                  },
                  "attach_time": null,
                  "remarks": ""
                }
                ]
            }
        '''
        center_id = str_to_int_or_default(request.query_params.get('center_id', 0), 0)
        group_id = str_to_int_or_default(request.query_params.get('group_id', 0), 0)
        host_id = str_to_int_or_default(request.query_params.get('host_id', 0), 0)
        type_val = str_to_int_or_default(request.query_params.get('type', 0), 0)
        search = str_to_int_or_default(request.query_params.get('search', 0), 0)

        user = request.user
        if not (user and user.is_authenticated):
            return Response(data={'code': 401, 'code_text': '未身份认证，无权限'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            queryset = PCIDeviceManager().filter_pci_queryset(center_id=center_id, group_id=group_id, host_id=host_id,
                       type_id=type_val, search=search, user=user, related_fields=('host', 'vm'))
        except DeviceError as e:
            return Response(data={'code': 400, 'code_text': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary='查询主机可挂载的PCI设备',
        request_body=no_body,
        responses={
            201: """
                    {
                        "code": 201,
                        "code_text": "挂载设备成功"
                    }
                """
        }
    )
    @action(methods=['get'], detail=False, url_path=r'vm/(?P<vm_uuid>[0-9a-z-]+)', url_name='vm_can_mount')
    def vm_can_mount(self, request, *args, **kwargs):
        """
        查询主机可挂载的PCI设备

            http code 200:
            {
              "count": 1,
              "next": null,
              "previous": null,
              "results": [
                {
                  "id": 1,
                  "type": {
                    "val": 1,
                    "name": "GPU"
                  },
                  "vm": {                           # 已挂载于主机；未挂载时为 null
                    "uuid": "c6c8f333bc9c426dad04a040ddd44b47",
                    "ipv4": "10.107.50.15"
                  },
                  "host": {
                    "id": 1,
                    "ipv4": "10.100.50.121"
                  },
                  "attach_time": "2020-03-11T11:38:05.102522+08:00",    # 挂载时间； 未挂载时为 null
                  "remarks": ""
                }
              ]
            }
            http code 400:
            {
                "code": 400,
                "code_text": "xxx"
            }
        """
        vm_uuid = kwargs.get('vm_uuid', '')

        try:
            vm = VmManager().get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=('host', ))
        except VmError as e:
            return Response(data={'code': 400, 'code_text': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if not vm:
            return Response({'code': 404, 'code_text': '云主机不存在'}, status=status.HTTP_404_NOT_FOUND)

        try:
            queryset = PCIDeviceManager().get_pci_queryset_by_host(host=vm.host)
            queryset = queryset.select_related('host', 'vm').all()
        except DeviceError as e:
            return Response(data={'code': 400, 'code_text': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary='挂载PCI设备',
        request_body=no_body,
        manual_parameters=[
            openapi.Parameter(
                name='vm_uuid',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=True,
                description='虚拟机uuid'
            )
        ],
        responses={
            201: """
                {
                    "code": 201,
                    "code_text": "挂载设备成功"
                }
            """
        }
    )
    @action(methods=['post'], detail=True, url_path='mount', url_name='mount-pci')
    def mount_pci(self, request, *args, **kwargs):
        '''
        挂载PCI设备

            http code 201:
            {
                "code": 201,
                "code_text": "挂载设备成功"
            }
            http code 400:
            {
                "code": 400,
                "code_text": "挂载设备失败，xxx"
            }

        '''
        dev_id = str_to_int_or_default(kwargs.get(self.lookup_field, 0), 0)
        vm_uuid = request.query_params.get('vm_uuid', '')
        if dev_id <= 0:
            return Response(data={'code': 400, 'code_text': '无效的设备ID'}, status=status.HTTP_400_BAD_REQUEST)
        if not vm_uuid:
            return Response(data={'code': 400, 'code_text': '无效的虚拟机ID'}, status=status.HTTP_400_BAD_REQUEST)
        try:
             dev = VmAPI().mount_pci_device(vm_uuid=vm_uuid, device_id=dev_id, user=request.user)
        except VmError as e:
            return Response(data={'code': 400, 'code_text': f'挂载失败，{str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data={'code': 201, 'code_text': '挂载成功'}, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary='卸载PCI设备',
        request_body=no_body,
        responses={
            201: """
                {
                    "code": 201,
                    "code_text": "卸载设备成功"
                }
            """
        }
    )
    @action(methods=['post'], detail=True, url_path='umount', url_name='umount-pci')
    def umount_pci(self, request, *args, **kwargs):
        '''
        卸载PCI设备

            http code 201:
            {
                "code": 201,
                "code_text": "卸载设备成功"
            }
            http code 400:
            {
                "code": 400,
                "code_text": "卸载设备失败，xxx"
            }

        '''
        dev_id = str_to_int_or_default(kwargs.get(self.lookup_field, 0), 0)
        if dev_id <= 0:
            return Response(data={'code': 400, 'code_text': '无效的设备ID'}, status=status.HTTP_400_BAD_REQUEST)

        try:
             dev = VmAPI().umount_pci_device(device_id=dev_id, user=request.user)
        except VmError as e:
            return Response(data={'code': 400, 'code_text': f'卸载失败，{str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data={'code': 201, 'code_text': '卸载成功'}, status=status.HTTP_201_CREATED)

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        Defaults to using `self.serializer_class`.
        Custom serializer_class
        """
        if self.action in ['list', 'retrieve', 'vm_can_mount']:
            return serializers.PCIDeviceSerializer
        return Serializer


class MacIPViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, ]
    pagination_class = LimitOffsetPagination

    @swagger_auto_schema(
        operation_summary='获取mac ip列表',
        manual_parameters=[
            openapi.Parameter(
                name='vlan_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='筛选条件，子网id'
            ),
            openapi.Parameter(
                name='used',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_BOOLEAN,
                required=False,
                description='筛选条件，false(可用的未分配的)，其他值等同true(已分配的)'
            )
        ],

    )
    def list(self, request, *args, **kwargs):
        '''
        获取mac ip列表

            http code 200:
                {
                  "count": 1,
                  "next": null,
                  "previous": null,
                  "results": [
                    {
                      "id": 1,
                      "mac": "C8:00:0A:6B:32:FD",
                      "ipv4": "10.107.50.253",
                      "used": true
                    }
                  ]
                }
        '''
        vlan_id = request.query_params.get('vlan_id', None)
        if vlan_id is not None:
            vlan_id = str_to_int_or_default(vlan_id, None)

        used = request.query_params.get('used', None)
        if used is not None:
            used = False if (used.lower() == 'false') else True

        queryset = MacIPManager().filter_macip_queryset(vlan=vlan_id, used=used)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.MacIPSerializer
        return Serializer


class FlavorViewSet(viewsets.GenericViewSet):
    """
    虚拟机硬件配置样式视图
    """
    permission_classes = [IsAuthenticated, ]
    pagination_class = LimitOffsetPagination

    @swagger_auto_schema(
        operation_summary='列举硬件配置样式',
        request_body=no_body
    )
    def list(self, request, *args, **kwargs):
        """
        获取mac ip列表

            http code 200:
                {
                  "count": 1,
                  "next": null,
                  "previous": null,
                  "results": [
                    {
                      "id": 1,
                      "vcpus": 1,
                      "ram": 1024           # MB
                    }
                  ]
                }
        """
        queryset = FlavorManager().get_user_flaver_queryset(user=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({'results': serializer.data})

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.FlavorSerializer
        return Serializer

