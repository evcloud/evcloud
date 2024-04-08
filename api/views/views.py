from django.conf import settings
from rest_framework import status
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

from ceph.models import GlobalConfig
from logrecord.manager import user_operation_record
from vms.manager import VmManager, VmError, FlavorManager
from vms.api import VmAPI
from vms.migrate import VmMigrateManager
from novnc.manager import NovncTokenManager, NovncError
from compute.models import Center, Group, Host
from compute.managers import HostManager, CenterManager, GroupManager, ComputeError
from network.managers import VlanManager
from network.managers import MacIPManager
from image.managers import ImageManager
from vdisk.models import Vdisk
from vdisk.manager import VdiskManager, VdiskError
from device.manager import PCIDeviceManager, DeviceError
from vpn.manager import VPNManager, VPNError
from api import serializers
from utils import errors as exceptions
from utils.vm_normal_status import vm_normal_status
from api.paginations import MacIpLimitOffsetPagination
from api.viewsets import CustomGenericViewSet
from version import __version__
from logrecord.models import LogRecord

VPN_USER_ACTIVE_DEFAULT = getattr(settings, 'VPN_USER_ACTIVE_DEFAULT', False)


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
    except Exception:
        pass

    return msg


def str_to_int_or_default(val, default):
    """
    字符串转int，转换失败返回设置的默认值

    :param val: 待转化的字符串
    :param default: 转换失败返回的值
    :return:
        int     # success
        default # failed
    """
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


class VmsViewSet(CustomGenericViewSet):
    """
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
              "uuid": "7ee56c2b242c41c3890b23e18dc5194b",
              "name": "7ee56c2b242c41c3890b23e18dc5194b",
              "vcpu": 1,
              "mem": 1024,
              "image": "centos7",
              "disk": "7ee56c2b242c41c3890b23e18dc5194b",
              "sys_disk_size": 8,
              "host": "10.193.36.121",
              "mac_ip": "192.168.100.3",
              "ip": {
                "ipv4": "192.168.100.3",
                "public_ipv4": false,
                "ipv6": null
              },
              "user": {
                "id": 1,
                "username": "wanghuang"
              },
              "create_time": "2023-07-27T15:54:25.383633+08:00",
              "mem_unit": "MB"
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
            "sys_disk_size": 100,
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
            "image": "CentOS_8",
            "image_info": {
              "id": 4,
              "name": "CentOS_8",
              "desc": "",
              "default_user": "root",
              "default_password": "cnic.cn"
            },
            "disk": "5b1f9a09b7224bdeb2ae12678ad0b1d4",
            "sys_disk_size": 100,
            "host": "10.100.50.121",
            "mac_ip": "10.107.50.253",
            "ip": {
              "ipv4": "10.107.50.22",
              "public_ipv4": false,
              "ipv6": null,
            },
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
            ],
            "host_info": {
              "id": 4,
              "ipv4": "10.0.200.83",
              "group": {
                "id": 4
              }
            }
          }
        }
        >>Http Code: 状态码400：请求失败;
            {
                'code': 400,
                'code_text': 'xxx失败'
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
    """
    permission_classes = [IsAuthenticated, ]
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
                description='所属数据中心id'
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
            ),
            openapi.Parameter(
                name='mem_unit',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description='内存计算单位（默认MB，可选GB）'
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        center_id = str_to_int_or_default(request.query_params.get('center_id', 0), default=0)
        group_id = str_to_int_or_default(request.query_params.get('group_id', 0), default=0)
        host_id = str_to_int_or_default(request.query_params.get('host_id', 0), default=0)
        user_id = str_to_int_or_default(request.query_params.get('user_id', 0), default=0)
        search = request.query_params.get('search', '')

        mem_unit = str.upper(request.query_params.get('mem_unit', 'UNKNOWN'))
        if mem_unit not in ['GB', 'MB', 'UNKNOWN']:
            exc = exceptions.BadRequestError(msg='无效的内存单位, 正确格式为GB、MB或为空')
            return self.exception_response(exc)

        user = request.user
        manager = VmManager()
        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.SELECT,
                                      operation_content='查询云主机列表', remark='')
        try:
            if user.is_superuser:  # 当前是超级用户，user_id查询参数有效
                self.queryset = manager.filter_vms_queryset(center_id=center_id, group_id=group_id, host_id=host_id,
                                                            search=search, user_id=user_id, all_no_filters=True)
            else:
                self.queryset = manager.filter_vms_queryset(center_id=center_id, group_id=group_id, host_id=host_id,
                                                            search=search, user_id=user.id)
        except VmError as e:
            exc = exceptions.BadRequestError(msg=f'查询虚拟机时错误, {e}')
            return self.exception_response(exc)

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, context={'mem_unit': mem_unit}, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, context={'mem_unit': mem_unit}, many=True)
        data = {'results': serializer.data}
        return Response(data)

    @swagger_auto_schema(
        operation_summary='查询PCI设备可挂载的虚拟机',
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
                  "uuid": "7ee56c2b242c41c3890b23e18dc5194b",
                  "name": "7ee56c2b242c41c3890b23e18dc5194b",
                  "vcpu": 1,
                  "mem": 1024,
                  "image": "centos7",
                  "disk": "7ee56c2b242c41c3890b23e18dc5194b",
                  "sys_disk_size": 8,
                  "host": "10.193.36.121",
                  "mac_ip": "192.168.100.3",
                  "ip": {
                    "ipv4": "192.168.100.3",
                    "public_ipv4": false,
                    "ipv6": null
                  },
                  "user": {
                    "id": 1,
                    "username": "wanghuang"
                  },
                  "create_time": "2023-07-27T15:54:25.383633+08:00",
                  "mem_unit": "MB"
                },
              ]
            }
        """
        pci_id = str_to_int_or_default(kwargs.get('pci_id', 0), 0)
        if pci_id <= 0:
            exc = exceptions.BadRequestError(msg='无效的PCI ID')
            return self.exception_response(exc)

        mem_unit = str.upper(request.query_params.get('mem_unit', 'UNKNOWN'))
        if mem_unit not in ['GB', 'MB', 'UNKNOWN']:
            exc = exceptions.BadRequestError(msg='无效的内存单位, 正确格式为GB、MB或为空')
            return self.exception_response(exc)

        try:
            dev = PCIDeviceManager().get_device_by_id(device_id=pci_id)
        except DeviceError as exc:
            exc.msg = f'查询PCI设备错误，{str(exc)}'
            return self.exception_response(exc)

        if not dev:
            exc = exceptions.DeviceNotFound(msg='PCI设备不存在')
            return self.exception_response(exc)

        host = dev.host
        user = request.user
        mgr = VmManager()
        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.SELECT,
                                      operation_content='查询PCI设备可挂载的虚拟机', remark='')
        try:
            qs = mgr.get_vms_queryset_by_host(host)
            qs = qs.select_related('user', 'image', 'mac_ip', 'host')
            if not user.is_superuser:
                qs = qs.filter(user=user).all()
        except VmError as e:
            e.msg = f'查询主机错误，{str(e)}'
            return self.exception_response(e)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, context={'mem_unit': mem_unit}, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, context={'mem_unit': mem_unit}, many=True)
        data = {'results': serializer.data}
        return Response(data)

    @swagger_auto_schema(
        operation_summary='查询硬盘可挂载的虚拟机',
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
                  "sys_disk_size": 100,
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
            exc = exceptions.BadRequestError(msg='无效的VDisk UUID')
            return self.exception_response(exc)
        mem_unit = str.upper(request.query_params.get('mem_unit', 'UNKNOWN'))
        if mem_unit not in ['GB', 'MB', 'UNKNOWN']:
            exc = exceptions.BadRequestError(msg='无效的内存单位, 正确格式为GB、MB或为空')
            return self.exception_response(exc)

        try:
            vdisk = VdiskManager().get_vdisk_by_uuid(uuid=vdisk_uuid, related_fields=('quota__group',))
        except DeviceError as e:
            e.msg = f'查询硬盘错误，{str(e)}'
            return self.exception_response(e)

        if not vdisk:
            return self.exception_response(exceptions.VdiskNotExist())

        center_id = vdisk.quota.group.center_id
        user = request.user
        mgr = VmManager()
        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.SELECT,
                                      operation_content='查询硬盘可挂载的虚拟机', remark='')
        try:
            if user.is_superuser:
                queryset = mgr.filter_vms_queryset(center_id=center_id,
                                                   related_fields=('user', 'image', 'mac_ip', 'host'))
            else:
                queryset = mgr.filter_vms_queryset(center_id=center_id, user_id=user.id,
                                                   related_fields=('user', 'image', 'mac_ip', 'host'))
        except VmError as e:
            e.msg = f'查询主机错误，{str(e)}'
            return self.exception_response(e)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, context={'mem_unit': mem_unit}, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, context={'mem_unit': mem_unit}, many=True)
        data = {'results': serializer.data}
        return Response(data)

    @swagger_auto_schema(
        operation_summary='创建虚拟机',
        manual_parameters=[
            openapi.Parameter(
                name='ip-type',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description='指定分配IP类型，可选值public（公网）、 private（私网）'
            ),
            openapi.Parameter(
                name='mem_unit',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description='内存计算单位（默认MB，可选GB）'
            )
        ],
        responses={
            201: ''
        }
    )
    def create(self, request, *args, **kwargs):
        ip_type = request.query_params.get('ip-type', None)
        if ip_type is None:
            ip_public = None
        elif ip_type == 'public':
            ip_public = True
        elif ip_type == 'private':
            ip_public = False
        else:
            exc = exceptions.BadRequestError(msg='参数ip-type的值无效')
            return self.exception_response(exc)

        mem_unit = str.upper(request.query_params.get('mem_unit', 'UNKNOWN'))
        if mem_unit == 'UNKNOWN':
            mem_unit = str.upper(request.data.get('mem_unit', 'UNKNOWN'))

        if mem_unit not in ['GB', 'MB', 'UNKNOWN']:
            exc = exceptions.BadRequestError(msg='无效的内存单位, 正确格式为GB、MB或为空')
            return self.exception_response(exc)

        serializer = self.get_serializer(data=request.data, context={'mem_unit': mem_unit})
        if not serializer.is_valid(raise_exception=False):
            code_text = serializer_error_msg(errors=serializer.errors, default='参数验证有误')
            exc = exceptions.BadRequestError(msg=code_text)
            data = exc.data()
            data['data'] = serializer.data
            return Response(data, status=exc.status_code)

        validated_data = serializer.validated_data
        # 配置样式
        flavor_id = validated_data.pop('flavor_id', None)
        if flavor_id:
            flavor = FlavorManager().get_flavor_by_id(flavor_id)
            if not flavor:
                exc = exceptions.NotFoundError(msg='配置样式flavor不存在')
                data = exc.data()
                data['data'] = serializer.data
                return Response(data, status=exc.status_code)
            else:
                validated_data['vcpu'] = flavor.vcpus
                validated_data['mem'] = flavor.ram  # 单位为GB

        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.ADDITION,
                                      operation_content='创建云主机', remark=validated_data['remarks'])
        api = VmAPI()
        try:
            vm = api.create_vm(user=request.user, **validated_data, ip_public=ip_public)
        except VmError as e:
            data = e.data()
            data['data'] = serializer.data
            return Response(data, status=status.HTTP_200_OK)

        return Response(data={
            'code': 201,
            'code_text': '创建成功',
            'data': request.data,
            'vm': serializers.VmSerializer(vm, context={'mem_unit': mem_unit}).data
        }, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary='获取虚拟机详细信息',
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
    def retrieve(self, request, *args, **kwargs):

        mem_unit = str.upper(request.query_params.get('mem_unit', 'UNKNOWN'))
        if mem_unit not in ['GB', 'MB', 'UNKNOWN']:
            exc = exceptions.BadRequestError(msg='无效的内存单位, 正确格式为GB、MB或为空')
            return self.exception_response(exc)

        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.SELECT,
                                      operation_content='获取云主机详细信息', remark='')
        vm_uuid = kwargs.get(self.lookup_field, '')
        try:
            vm = VmManager().get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=('image', 'mac_ip', 'host', 'user'))
        except VmError as e:
            return Response(data=e.data(), status=e.status_code)

        if not vm:
            return Response(data=exceptions.VmNotExistError(msg='虚拟机不存在').data(),
                            status=status.HTTP_404_NOT_FOUND)
        if not vm.user_has_perms(user=request.user):
            return Response(data=exceptions.VmAccessDeniedError(msg='当前用户没有权限访问此虚拟机').data(),
                            status=status.HTTP_403_FORBIDDEN)

        # 搁置虚拟机，不允许
        # status_bool = vm_normal_status(vm=vm)
        # if status_bool is False:
        #     return self.exception_response(exceptions.VmAccessDeniedError(msg='虚拟机搁置状态， 拒绝此操作'))

        return Response(data={
            'code': 200,
            'code_text': '获取虚拟机信息成功',
            'vm': self.get_serializer(vm, context={'mem_unit': mem_unit}).data
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
        """
        删除虚拟机

            >> Http Code: 状态码204：删除成功，NO_CONTENT；
            >> Http Code: 状态码404：找不到vm资源; "err_code" = "VmNotExist"
                         状态码409：需要先关闭vm;
                         状态码500：删除虚拟机失败,服务器内部错误;
                {
                    "code": xxx,
                    "code_text": "xxx"
                    "err_code": "xxx"
                }
        """
        vm_uuid = kwargs.get(self.lookup_field, '')
        force = request.query_params.get('force', '').lower()
        force = True if force == 'true' else False
        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.DELETION,
                                      operation_content='删除云主机', remark='')
        api = VmAPI()
        try:
            api.delete_vm(user=request.user, vm_uuid=vm_uuid, force=force)
        except VmError as e:
            return Response(data=e.data(), status=e.code)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_summary='修改虚拟机vcpu和内存大小',
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
            200: """
                {
                    "code": 200,
                    "code_text": "修改虚拟机成功"
                }
            """
        }
    )
    def partial_update(self, request, *args, **kwargs):
        """
        修改虚拟机vcpu和内存大小

            指定flavor或者直接指定vcpu和mem, 优先使用flavor

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
        """
        vm_uuid = kwargs.get(self.lookup_field, '')
        mem_unit = str.upper(request.data.get('mem_unit', 'UNKNOWN'))
        if mem_unit not in ['GB', 'MB', 'UNKNOWN']:
            exc = exceptions.BadRequestError(msg='无效的内存单位, 正确格式为GB、MB或为空')
            return self.exception_response(exc)

        serializer = self.get_serializer(data=request.data, context={'mem_unit': mem_unit})
        if not serializer.is_valid(raise_exception=False):
            code_text = serializer_error_msg(serializer.errors, '参数验证有误')
            exc = exceptions.BadRequestError(msg=code_text)
            data = exc.data()
            data['data'] = serializer.data
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.CHANGE,
                                      operation_content='修改云主机vcpu和内存大小', remark='')
        # 配置样式
        data = serializer.validated_data
        flavor_id = data.get('flavor_id')
        vcpu = data.get('vcpu', None)
        mem = data.get('mem', None)

        if not vcpu:
            vcpu = 0

        if not mem:
            mem = 0

        if flavor_id:
            flavor = FlavorManager().get_flavor_by_id(flavor_id)
            if not flavor:
                exc = exceptions.NotFoundError(msg='配置样式flavor不存在')
                data = exc.data()
                data['data'] = serializer.data
                return Response(data, status=status.HTTP_404_NOT_FOUND)
            else:
                vcpu = flavor.vcpus
                mem = flavor.ram

        api = VmAPI()
        try:
            api.edit_vm_vcpu_mem(user=request.user, vm_uuid=vm_uuid, mem=mem, vcpu=vcpu)
        except VmError as e:
            return Response(data=e.data(), status=e.status_code)

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
            200: """
            {
                'code': 200,
                'code_text': '操作虚拟机成功'
            }
            """,
        }
    )
    @action(methods=['patch'], url_path='operations', detail=True, url_name='vm-operations')
    def vm_operations(self, request, *args, **kwargs):
        """
        操作虚拟机

            >>Http Code: 状态码200：请求成功;
                {
                    'code': 200,
                    'code_text': '操作虚拟机成功'
                }
            >>Http Code: 400, 403, 404, 409, 500：请求失败;
                {
                    "code": xxx,
                    "code_text": "xxx",
                    "err_code": "xxx"           # "VmNotExist", "Error", "InvalidParam"
                }
        """
        vm_uuid = kwargs.get(self.lookup_field, '')
        try:
            op = request.data.get('op', None)
        except Exception as e:
            exc = exceptions.BadRequestError(msg=f'参数有误，{str(e)}')
            return self.exception_response(exc)

        ops = ['start', 'reboot', 'shutdown', 'poweroff', 'delete', 'delete_force']
        if not op or op not in ops:
            exc = exceptions.InvalidParamError(msg='op参数无效')
            return self.exception_response(exc)

        ops_dict = {
            'start': '启动云主机',
            'reboot': '重启云主机',
            'shutdown': '关闭云主机',
            'poweroff': '云主机断电',
            'delete': '删除云主机',
            'delete_force': '强制删除云主机',
        }

        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.CHANGE,
                                      operation_content=ops_dict[op], remark='')

        api = VmAPI()
        try:
            ok = api.vm_operations(user=request.user, vm_uuid=vm_uuid, op=op)
        except VmError as e:
            return self.exception_response(e)

        if not ok:
            return self.exception_response(exceptions.VmError(msg=f'{op}虚拟机失败'))

        return Response(data={'code': 200, 'code_text': f'{op}虚拟机成功'})

    @swagger_auto_schema(
        operation_summary='获取虚拟机当前运行状态',
        request_body=no_body,
        responses={
            200: """
            {
              "code": 200,
              "code_text": "获取信息成功",
              "status": {
                "status_code": 5,
                "status_text": "shut off"
              }
            }
            """,
            "400, 403, 404, 409, 500": """
            {
                "code": xxx,
                "code_text": "xxx",
                "err_code": "xxx"           # "VmNotExist", "Error"
            }
            """,
        }
    )
    @action(methods=['get'], url_path='status', detail=True, url_name='vm-status')
    def vm_status(self, request, *args, **kwargs):
        vm_uuid = kwargs.get(self.lookup_field, '')
        api = VmAPI()

        # user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.SELECT,
        #                               operation_content='获取云主机当前运行状态', remark='')
        try:
            code, msg = api.get_vm_status(user=request.user, vm_uuid=vm_uuid)
        except VmError as e:
            e.msg = f'获取虚拟机状态失败，{str(e)}'
            return self.exception_response(e)

        return Response(data={'code': 200, 'code_text': '获取虚拟机状态成功',
                              'status': {'status_code': code, 'status_text': msg}})

    @swagger_auto_schema(
        operation_summary='创建虚拟机vnc',
        request_body=no_body,
        responses={
            200: """
            {
              "code": 200,
              "code_text": "创建虚拟机vnc成功",
              "vnc": {
                "id": "42bfe71e-6419-474a-bc99-9e519637797d",
                "url": "http://159.226.91.140:8000/novnc/?vncid=42bfe71e-6419-474a-bc99-9e519637797d"
              }
            }
            """
        }
    )
    @action(methods=['post'], url_path='vnc', detail=True, url_name='vm-vnc')
    def vm_vnc(self, request, *args, **kwargs):
        """
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
        """
        vm_uuid = kwargs.get(self.lookup_field, '')
        try:
            vm = VmManager().get_vm_by_uuid(vm_uuid=vm_uuid)
        except VmError as e:
            return self.exception_response(e)

        if not vm:
            return Response(data=exceptions.VmNotExistError(msg='虚拟机不存在').data(),
                            status=status.HTTP_404_NOT_FOUND)
        if not vm.user_has_perms(user=request.user):
            return Response(data=exceptions.VmAccessDeniedError(msg='当前用户没有权限访问此虚拟机').data(),
                            status=status.HTTP_403_FORBIDDEN)

        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.ADDITION,
                                      operation_content='创建云主机vnc', remark='')
        # 搁置虚拟机，不允许
        status_bool = vm_normal_status(vm=vm)
        if status_bool is False:
            return self.exception_response(exceptions.VmAccessDeniedError(msg='虚拟机搁置状态， 拒绝此操作'))

        vm_uuid = vm.get_uuid()
        host_ipv4 = vm.host.ipv4
        sshkey = vm.host.group.center.ssh_key

        vnc_manager = NovncTokenManager()
        try:
            vnc_id, url = vnc_manager.generate_token(vmid=vm_uuid, hostip=host_ipv4, sshkey=sshkey)
        except NovncError as e:
            e.msg = f'创建虚拟机vnc失败，{str(e)}'
            return self.exception_response(e)

        http_host = request.META['HTTP_HOST']
        # http_host = http_host.split(':')[0]
        http_scheme = 'https'
        global_config_obj = GlobalConfig().get_global_config()
        if global_config_obj:
            http_scheme = global_config_obj.novnchttp
        url = f'{http_scheme}://{http_host}{url}'
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
            200: """
            {
                'code': 200,
                'code_text': '修改虚拟机备注信息成功'
            }
            """,
            "400, 403, 500": """
                {
                    'code': xxx,
                    'code_text': 'xxx',
                    "err_code": "xxx"
                }
                """
        }
    )
    @action(methods=['patch'], url_path='remark', detail=True, url_name='vm-remark')
    def vm_remark(self, request, *args, **kwargs):
        """
        修改虚拟机备注信息
        """
        remark = request.query_params.get('remark', None)
        if remark is None:
            exc = exceptions.BadRequestError(msg='参数有误，无效的备注信息')
            return self.exception_response(exc)

        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.CHANGE,
                                      operation_content='修改虚拟机备注信息', remark=remark)
        vm_uuid = kwargs.get(self.lookup_field, '')
        api = VmAPI()
        try:
            api.modify_vm_remark(user=request.user, vm_uuid=vm_uuid, remark=remark)
        except VmError as e:
            e.msg = f'修改虚拟机备注信息失败，{str(e)}'
            return self.exception_response(e)

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
            201: """
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
            """,
            '400, 403, 404, 500': """
            {
                'code': 400,
                'code_text': 'xxx',
                "err_code": "xxx"
            }
            """
        }
    )
    @action(methods=['post'], url_path='snap', detail=True, url_name='vm-sys-snap')
    def vm_sys_snap(self, request, *args, **kwargs):
        """
        创建虚拟机系统盘快照
        """
        remark = request.query_params.get('remark', '')
        vm_uuid = kwargs.get(self.lookup_field, '')
        api = VmAPI()

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.ADDITION,
                                      operation_content='创建云主机系统盘快照', remark=remark)

        try:
            snap = api.create_vm_sys_snap(vm_uuid=vm_uuid, remarks=remark, user=request.user)
        except VmError as e:
            e.msg = f'创建虚拟机系统快照失败，{str(e)}'
            return self.exception_response(e)

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
            204: """SUCCESS NO CONTENT""",
            '400, 403, 404, 500': """
                {
                    'code': xxx,
                    'code_text': 'xxx',
                    "err_code": "xxx"
                }
            """
        }
    )
    @action(methods=['delete'], url_path=r'snap/(?P<id>[0-9]+)', detail=False, url_name='delete-vm-snap')
    def delete_vm_snap(self, request, *args, **kwargs):
        """
        删除一个虚拟机系统快照
        """
        snap_id = str_to_int_or_default(kwargs.get('id', '0'), default=0)
        if snap_id <= 0:
            exc = exceptions.BadRequestError(msg='无效的id参数')
            return self.exception_response(exc)

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.ADDITION,
                                      operation_content='删除一个云主机系统快照', remark='')
        try:
            VmAPI().delete_sys_disk_snap(snap_id=snap_id, user=request.user)
        except VmError as e:
            e.msg = f'删除虚拟机系统快照失败，{str(e)}'
            return self.exception_response(e)
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
            200: """
                {
                    'code': 200,
                    'code_text': '修改快照备注信息成功'
                }
            """,
            '400, 403, 404, 500': """
                {
                    'code': xxx,
                    'code_text': 'xxx',
                    "err_code": "xxx"
                }
            """
        }
    )
    @action(methods=['patch'], url_path=r'snap/(?P<id>[0-9]+)/remark', detail=False, url_name='vm-snap-remark')
    def vm_snap_remark(self, request, *args, **kwargs):
        """
        修改虚拟机快照备注信息
        """
        remark = request.query_params.get('remark', None)
        if remark is None:
            exc = exceptions.BadRequestError(msg='参数有误，无效的备注信息')
            return self.exception_response(exc)

        snap_id = str_to_int_or_default(kwargs.get('id', '0'), default=0)
        if snap_id <= 0:
            exc = exceptions.BadRequestError(msg='无效的id参数')
            return self.exception_response(exc)

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.CHANGE,
                                      operation_content='修改云主机快照备注信息', remark=remark)
        try:
            VmAPI().modify_sys_snap_remarks(snap_id=snap_id, remarks=remark, user=request.user)
        except VmError as e:
            e.msg = f'修改快照备注信息失败，{str(e)}'
            return self.exception_response(e)

        return Response(data={'code': 200, 'code_text': '修改快照备注信息成功'})

    @swagger_auto_schema(
        operation_summary='虚拟机系统盘回滚到指定快照',
        request_body=no_body,
        responses={
            201: """
            {
                'code': 201,
                'code_text': '回滚虚拟机成功'
            }
            """,
            '400, 403, 404, 409, 500': """
            {
                'code': xxx,
                'code_text': 'xxx',
                "err_code": "xxx"
            }
            """
        }
    )
    @action(methods=['post'], url_path=r'rollback/(?P<snap_id>[0-9]+)', detail=True, url_name='vm-rollback-snap')
    def vm_rollback_snap(self, request, *args, **kwargs):
        """
        虚拟机系统盘回滚到指定快照
        """
        vm_uuid = kwargs.get(self.lookup_field, '')
        snap_id = str_to_int_or_default(kwargs.get('snap_id', '0'), default=0)
        if snap_id <= 0:
            exc = exceptions.BadRequestError(msg='无效的id参数')
            return self.exception_response(exc)

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.CHANGE,
                                      operation_content='云主机系统盘回滚到指定快照', remark='')
        api = VmAPI()
        try:
            api.vm_rollback_to_snap(vm_uuid=vm_uuid, snap_id=snap_id, user=request.user)
        except VmError as e:
            e.msg = f'回滚虚拟机失败，{str(e)}'
            return self.exception_response(e)

        return Response(data={'code': 201, 'code_text': '回滚虚拟机成功'}, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary='更换虚拟机系统',
        request_body=no_body,
        responses={
            201: """
                {
                    'code': 201,
                    'code_text': '更换虚拟机系统成功'
                }
                """,
            '400, 403, 404, 409, 500': """
                {
                    'code': xxx,
                    'code_text': 'xxx',
                    "err_code": "xxx"
                }
                """
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
            exc = exceptions.BadRequestError(msg='无效的image_id参数')
            return self.exception_response(exc)

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.REBUILD,
                                      operation_content='重建云主机系统', remark='')
        api = VmAPI()
        try:
            api.change_sys_disk(vm_uuid=vm_uuid, image_id=image_id, user=request.user)
        except VmError as e:
            e.msg = f'更换虚拟机系统失败，{str(e)}'
            return self.exception_response(e)

        return Response(data={'code': 201, 'code_text': '更换虚拟机系统成功'}, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary='静态迁移虚拟机到指定宿主机',
        request_body=no_body,
        manual_parameters=[
            openapi.Parameter(
                name='force',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_BOOLEAN,
                required=False,
                description="true: 强制迁移；其他忽略"
            )
        ],
        responses={
            201: """
                    {
                        'code': 201,
                        'code_text': '迁移虚拟机成功'
                    }
                    """,
            400: """
                    {
                        'code': 400,
                        'code_text': 'xxx'
                    }
                    """
        }
    )
    @action(methods=['post'], url_path=r'migrate/(?P<host_id>[0-9]+)', detail=True, url_name='vm_migrate')
    def vm_migrate(self, request, *args, **kwargs):
        """
        静态迁移虚拟机到指定宿主机
        """
        vm_uuid = kwargs.get(self.lookup_field, '')
        host_id = str_to_int_or_default(kwargs.get('host_id', '0'), default=0)
        if host_id <= 0:
            exc = exceptions.BadRequestError(msg='无效的host id参数')
            return self.exception_response(exc)

        force = request.query_params.get('force', '').lower()
        is_force = True if force == 'true' else False

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.MIGRATE,
                                      operation_content='静态迁移云主机到指定宿主机', remark='')
        api = VmAPI()
        try:
            api.migrate_vm(vm_uuid=vm_uuid, host_id=host_id, user=request.user, force=is_force)
        except VmError as e:
            e.msg = f'迁移虚拟机失败，{str(e)}'
            return self.exception_response(e)

        return Response(data={'code': 201, 'code_text': '迁移虚拟机成功'}, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary='动态迁移虚拟机到指定宿主机',
        request_body=no_body,
        responses={
            202: """
                {
                    'migrate_task': 'xxx'       # 异步迁移任务id,通过此id查询迁移任务的状态
                }
                """,
        }
    )
    @action(methods=['post'], url_path=r'live-migrate/(?P<host_id>[0-9]+)', detail=True, url_name='vm_migrate_live')
    def vm_migrate_live(self, request, *args, **kwargs):
        """
        动态迁移虚拟机到指定宿主机
        """
        vm_uuid = kwargs.get(self.lookup_field, '')
        host_id = str_to_int_or_default(kwargs.get('host_id', '0'), default=0)
        if host_id <= 0:
            exc = exceptions.BadRequestError(msg='无效的host id参数')
            return self.exception_response(exc)

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.MIGRATE,
                                      operation_content='动态迁移云主机到指定宿主机', remark='')

        api = VmAPI()
        try:
            m_task = api.live_migrate_vm(vm_uuid=vm_uuid, dest_host_id=host_id, user=request.user)
        except VmError as e:
            e.msg = f'迁移虚拟机失败，{str(e)}'
            return self.exception_response(e)

        return Response(data={'migrate_task': m_task.id}, status=status.HTTP_202_ACCEPTED)

    @swagger_auto_schema(
        operation_summary='修改虚拟机登录密码',
        responses={
            200: """
                {
                  "code": 200,
                  "code_text": "修改虚拟机登录密码成功",
                }
                """
        }
    )
    @action(methods=['post'], url_path='setpassword', detail=True, url_name='vm-change-password')
    def vm_change_password(self, request, *args, **kwargs):
        """
        修改虚拟机登录密码

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
            return self.exception_response(exceptions.BadRequestError(msg=msg))

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.CHANGE,
                                      operation_content='修改云主机登录密码', remark='')

        data = serializer.validated_data
        username = data.get('username')
        password = data.get('password')

        try:
            VmAPI().vm_change_password(vm_uuid=vm_uuid, user=request.user, username=username, password=password)
        except VmError as e:
            return self.exception_response(e)

        return Response(data={'code': 200, 'code_text': '修改虚拟机登录密码成功'})

    @swagger_auto_schema(
        operation_summary='尝试恢复丢失的虚拟机',
        request_body=no_body,
        responses={
            200: """"""
        }
    )
    @action(methods=['post'], url_path='miss-fix', detail=True, url_name='vm-miss-fix')
    def vm_miss_fix(self, request, *args, **kwargs):
        """
        虚拟机丢失修复

            >> http code 200:
            {
              "code": 200,
              "code_text": "成功修复丢失的虚拟机",
            }
            >> http code 403, 404, 409, 500
            {
                "code": xxx,
                "code_text": "xxx",
                "err_code": "xxx"
            }
            * err_code list:
                403: VmAccessDenied, 无权访问此虚拟主机;
                404: VmNotExist，无虚拟主机记录;
                409: VmAlreadyExist，虚拟主机未丢失，已存在无需修复;
                     VmDiskImageMiss, 系统盘镜像不存在，无法恢复此虚拟主机
                500: HostDown，宿主机无法访问
        """
        vm_uuid = kwargs.get(self.lookup_field, '')

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.CHANGE,
                                      operation_content='尝试恢复丢失的云主机', remark='')

        try:
            VmAPI().vm_miss_fix(vm_uuid=vm_uuid, user=request.user)
        except VmError as e:
            return Response(data=e.data(), status=e.status_code)

        return Response(data={'code': 200, 'code_text': '成功恢复丢失的虚拟机'})

    @swagger_auto_schema(
        operation_summary='查询虚拟机内存、网络io、硬盘io等性能信息',
        request_body=no_body,
        responses={
            200: """"""
        }
    )
    @action(methods=['get'], url_path='stats', detail=True, url_name='vm-stats')
    def vm_stats(self, request, *args, **kwargs):
        """
        查询虚拟机内存、网络io、硬盘io等性能信息

            >> http code 200:
            {
              "timestamp": 1625814253.1141162,
              "cpu_time_abs": 77520000000,
              "host_cpus": 128,
              "guest_cpus": 2,
              "total_mem_kb": 4194304,
              "cur_mem_kb": 590748,
              "disk_rd_kb": 227393,
              "disk_wr_kb": 105786,
              "net_tx_kb": 423,
              "net_rx_kb": 23985,
              "curr_mem_percent": 14.084529876708984
            }
            >> http code 403, 404, 409, 500
            {
                "code": xxx,
                "code_text": "xxx",
                "err_code": "xxx"
            }
            * err_code list:
                403: VmAccessDenied, 无权访问此虚拟主机;
                404: VmNotExist，无虚拟主机记录;
                500: HostDown，宿主机无法访问
        """
        vm_uuid = kwargs.get(self.lookup_field, '')

        # # 用户操作日志记录
        # user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.SELECT,
        #                               operation_content='查询云主机内存、网络io、硬盘io等性能信息', remark='')

        try:
            stats = VmAPI().get_vm_stats(vm_uuid=vm_uuid, user=request.user)
        except VmError as e:
            return Response(data=e.data(), status=e.status_code)

        return Response(data=stats)

    @swagger_auto_schema(
        operation_summary='虚拟机系统盘扩容',
        request_body=no_body,
        manual_parameters=[
            openapi.Parameter(
                name='expand-size',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=True,
                description="扩容大小，单位Gb"
            )
        ],
        responses={
            200: """"""
        }
    )
    @action(methods=['post'], url_path='sys-disk/expand', detail=True, url_name='vm-sys-disk-expand')
    def vm_sys_disk_expand(self, request, *args, **kwargs):
        """
        虚拟机系统盘扩容

            >> http code 200:
            {
                "sys_disk_size": 100        # 扩容后系统盘大小Gb
            }
            >> http code 403, 404, 409, 500
            {
                "code": xxx,
                "code_text": "xxx",
                "err_code": "xxx"
            }
            * err_code list:
                400: BadRequest, InvalidParam
                403: VmAccessDenied, 无权访问此虚拟主机;
                404: VmNotExist，无虚拟主机记录;
                500: HostDown，宿主机无法访问
        """
        vm_uuid = kwargs.get(self.lookup_field, '')
        expand_size = request.query_params.get('expand-size', None)
        if expand_size is None:
            return self.exception_response(
                exceptions.BadRequestError(msg='The query param "expand-size" is required'))

        try:
            expand_size = int(expand_size)
        except ValueError:
            return self.exception_response(
                exceptions.InvalidParamError(msg='The value of query param "expand-size" is invalid'))

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.CHANGE,
                                      operation_content='云主机系统盘扩容', remark='')

        try:
            vm = VmAPI().vm_sys_disk_expand(vm_uuid=vm_uuid, expand_size=expand_size, user=request.user)
        except VmError as e:
            return Response(data=e.data(), status=e.status_code)

        return Response(data={'sys_disk_size': vm.get_sys_disk_size()})

    @swagger_auto_schema(
        operation_summary='虚拟机搁置',
        request_body=no_body,
        responses={
            200: """"""
        }
    )
    @action(methods=['post'], url_path='shelve', detail=True, url_name='vm-shelve')
    def vm_shelve(self, request, *args, **kwargs):
        """虚拟机搁置"""
        vm_uuid = kwargs.get(self.lookup_field, '')
        api = VmAPI()

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.SHELVE,
                                      operation_content='云主机搁置', remark='')

        try:
            api.vm_shelve(vm_uuid=vm_uuid, user=request.user)
        except VmError as e:
            return Response(data=e.data(), status=e.status_code)
        return Response(data={'code': 201, 'code_text': '虚拟机已搁置'}, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary='搁置虚拟机恢复',
        request_body=no_body,
        manual_parameters=[
            openapi.Parameter(
                name='group_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description="指定宿主机组"
            ),
            openapi.Parameter(
                name='host_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description="指定宿主机"
            ),
            openapi.Parameter(
                name='mac_ip_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description="指定ip"
            ),
        ],
        responses={
            200: """"""
        }
    )
    @action(methods=['post'], url_path='unshelve', detail=True, url_name='vm-unshelve')
    def vm_unshelve(self, request, *args, **kwargs):
        """搁置虚拟机恢复"""
        vm_uuid = kwargs.get(self.lookup_field, '')
        host_id = str_to_int_or_default(request.query_params.get('host_id', '0'), default=0)
        mac_ip_id = str_to_int_or_default(request.query_params.get('mac_ip_id', '0'), default=0)
        group_id = str_to_int_or_default(request.query_params.get('group_id', '0'), default=0)
        api = VmAPI()

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.UNSHELVE,
                                      operation_content='云主机搁置恢复', remark='')

        try:
            vm = api.vm_unshelve(vm_uuid=vm_uuid, group_id=group_id, host_id=host_id, mac_ip_id=mac_ip_id,
                                 user=request.user)
        except VmError as e:
            return Response(data=e.data(), status=e.status_code)

        return Response(data={'code': 201, 'code_text': '搁置虚拟机已恢复'}, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary='搁置虚拟机列表',
        request_body=no_body,
        manual_parameters=[
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
                description='uuid - 备注 查询'
            ),
            openapi.Parameter(
                name='mem_unit',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description='内存计算单位（默认MB，可选GB）'
            )
        ],
        responses={
            200: """"""
        }
    )
    @action(methods=['get'], url_path='shelve', detail=False, url_name='vm-shelve-list')
    def vm_shelve_list(self, request, *args, **kwargs):
        """搁置虚拟机列表"""

        user_id = str_to_int_or_default(request.query_params.get('user_id', '0'), default=0)
        search = request.query_params.get('search', '')
        mem_unit = str.upper(request.query_params.get('mem_unit', 'UNKNOWN'))
        if mem_unit not in ['GB', 'MB', 'UNKNOWN']:
            exc = exceptions.BadRequestError(msg='无效的内存单位, 正确格式为GB、MB或为空')
            return self.exception_response(exc)

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.SELECT,
                                      operation_content='查询云主机搁置列表', remark='')

        user = request.user
        manager = VmManager()

        try:
            if user.is_superuser:  # 当前是超级用户，user_id查询参数有效
                self.queryset = manager.filter_shelve_vm_queryset(search=search, user_id=user_id, all_no_filters=True)
            else:
                self.queryset = manager.filter_shelve_vm_queryset(search=search, user_id=user.id)
        except VmError as e:
            exc = exceptions.BadRequestError(msg=f'查询虚拟机时错误, {e}')
            return self.exception_response(exc)

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, context={'mem_unit': mem_unit}, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, context={'mem_unit': mem_unit}, many=True)
        data = {'results': serializer.data}
        return Response(data)

    @swagger_auto_schema(
        operation_summary='删除搁置虚拟机',
        responses={
            204: 'SUCCESS NO CONTENT'
        }
    )
    @action(methods=['delete'], url_path='delshelve', detail=True, url_name='vm-unshelve-delete')
    def vm_shelve_destroy(self, request, *args, **kwargs):
        vm_uuid = kwargs.get(self.lookup_field, '')

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.DELETION,
                                      operation_content='删除搁置云主机', remark='')

        api = VmAPI()
        try:
            api.vm_delshelve(vm_uuid=vm_uuid, user=request.user)
        except VmError as e:
            return Response(data=e.data(), status=e.status_code)
        return Response(data={'code': 204, 'code_text': '虚拟机已删除'}, status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_summary='虚拟机附加ip',
        request_body=no_body,
        manual_parameters=[
            openapi.Parameter(
                name='ip_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='mac_ip'
            ),
        ],
        responses={
            204: 'SUCCESS NO CONTENT'
        }
    )
    @action(methods=['post'], url_path='attach', detail=True, url_name='vm-attach-ip')
    def vm_attach_ip(self, request, *args, **kwargs):
        """虚拟机附加ip"""
        vm_uuid = kwargs.get(self.lookup_field, '')
        ip_id = request.query_params.get('ip_id', None)
        if ip_id is not None:
            ip_id = str_to_int_or_default(ip_id, None)

        if ip_id is None:
            exc = exceptions.BadRequestError(msg='无效的id')
            return self.exception_response(exc)

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.ADDITION,
                                      operation_content='云主机附加IP', remark='')

        queryset = MacIPManager().get_macip_by_id(macip_id=ip_id)
        if not queryset or queryset.used or queryset.enable is False:
            exc = exceptions.BadRequestError(msg='无效的id')
            return self.exception_response(exc)

        api = VmAPI()
        try:
            api.attach_ip(vm_uuid=vm_uuid, user=request.user, mac_ip_obj=queryset)
        except VmError as e:
            return Response(data=e.data(), status=e.status_code)

        return Response(data={'code': 204, 'code_text': '虚拟机附加IP成功'}, status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_summary='虚拟机移除ip',
        request_body=no_body,
        manual_parameters=[
            openapi.Parameter(
                name='ip_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='mac_ip'
            ),
        ],
        responses={
            204: 'SUCCESS NO CONTENT'
        }
    )
    @action(methods=['post'], url_path='detach', detail=True, url_name='vm-detach-ip')
    def vm_detach_ip(self, request, *args, **kwargs):
        """虚拟机移除ip"""
        vm_uuid = kwargs.get(self.lookup_field, '')
        ip_id = request.query_params.get('ip_id', None)
        if ip_id is not None:
            ip_id = str_to_int_or_default(ip_id, None)

        if ip_id is None:
            exc = exceptions.BadRequestError(msg='无效的id')
            return self.exception_response(exc)

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.DELETION,
                                      operation_content='云主机移除IP', remark='')

        queryset = MacIPManager().get_macip_by_id(macip_id=ip_id)
        if not queryset or queryset.enable is False:
            exc = exceptions.BadRequestError(msg='无效的id')
            return self.exception_response(exc)

        api = VmAPI()
        try:
            api.detach_ip(vm_uuid=vm_uuid, user=request.user, mac_ip_obj=queryset)
        except VmError as e:
            return Response(data=e.data(), status=e.status_code)
        return Response(data={'code': 204, 'code_text': '虚拟机删除移除IP成功'}, status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_summary='虚拟机附加IP列表',
        responses={
            200: ''
        }
    )
    @action(methods=['get'], url_path='attach/list', detail=True, url_name='vm-attach-ip-list')
    def vm_attach_ip_list(self, request, *args, **kwargs):
        """
        虚拟机附加ip列表
        {
          "count": 2,
          "next": null,
          "previous": null,
          "results": [
            {
              "id": 30004,
              "vm": "1134ef74c09344bc9c1178ae8e7cde7b",
              "attach_ip": "192.168.100.11"
            },
            {
              "id": 30005,
              "vm": "1134ef74c09344bc9c1178ae8e7cde7b",
              "attach_ip": "192.168.100.12"
            }
          ]
        }

        """
        vm_uuid = kwargs.get(self.lookup_field, '')

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMS, action_flag=LogRecord.SELECT,
                                      operation_content='云主机附加IP列表', remark='')

        api = VmAPI()
        try:
            queryset = api.attach_ip_list(vm_uuid=vm_uuid, user=request.user)
        except VmError as e:
            return Response(data=e.data(), status=e.status_code)

        queryset = self.filter_queryset(queryset)

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
        if self.action in ['list', 'can_mount_pci', 'can_mount_vdisk']:
            return serializers.VmSerializer
        elif self.action == 'retrieve':
            return serializers.VmDetailSerializer
        elif self.action == 'create':
            return serializers.VmCreateSerializer
        elif self.action == 'partial_update':
            return serializers.VmPatchSerializer
        elif self.action == 'vm_change_password':
            return serializers.VmChangePasswordSerializer
        elif self.action == 'vm_shelve_list':
            return serializers.VmShelveListSerializer
        elif self.action == 'vm_attach_ip_list':
            return serializers.VmAttachListSerializer
        return Serializer


class CenterViewSet(CustomGenericViewSet):
    """
    数据中心类视图
    """
    permission_classes = [IsAuthenticated, ]
    pagination_class = LimitOffsetPagination
    queryset = Center.objects.all()

    def list(self, request, *args, **kwargs):
        """
        获取数据中心列表

            获取数据中心列表信息

            http code 200:
            {
              "count": 1,
              "next": null,
              "previous": null,
              "results": [
                {
                  "id": 1,
                  "name": "怀柔数据中心",
                  "location": "怀柔",
                  "desc": "xxx"
                }
              ]
            }
        """

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.DATACENTER, action_flag=LogRecord.SELECT,
                                      operation_content='获取数据中心列表', remark='')

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


class GroupViewSet(CustomGenericViewSet):
    """
    宿主机组类视图
    """
    permission_classes = [IsAuthenticated, ]
    pagination_class = LimitOffsetPagination
    queryset = Group.objects.filter(enable=True).all()

    @swagger_auto_schema(
        operation_summary='获取宿主机组列表',
        manual_parameters=[
            openapi.Parameter(
                name='center_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='所属数据中心id'
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """
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
            http code 400, 404, 500:
            {
              "code": xxx,
              "code_text": "xxx",
              "err_code": "xxx"
            }
        """
        center_id = str_to_int_or_default(request.query_params.get('center_id', 0), 0)
        if center_id < 0:
            exc = exceptions.BadRequestError(msg='center_id参数无效')
            return self.exception_response(exc)

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.HOST, action_flag=LogRecord.SELECT,
                                      operation_content='获取宿主机组列表', remark='')

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
            return self.exception_response(e)

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


class HostViewSet(CustomGenericViewSet):
    """
    宿主机类视图
    """
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
                name='mem_unit', in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description='内存计算单位（MB、GB、默认为MB）'
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        """
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
                  "vcpu_total": 24,
                  "vcpu_allocated": 14,
                  "mem_total": 132768,
                  "mem_allocated": 9216,
                  "vm_limit": 10,
                  "vm_created": 8,
                  "enable": true,
                  "desc": ""
                }
              ]
            }
        """
        group_id = int(request.query_params.get('group_id', 0))
        mem_unit = str.upper(request.query_params.get('mem_unit', 'UNKNOWN'))
        if mem_unit not in ['GB', 'MB', 'UNKNOWN']:
            exc = exceptions.BadRequestError(msg='无效的内存单位, 正确格式为GB、MB或为空')
            return self.exception_response(exc)

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.HOST, action_flag=LogRecord.SELECT,
                                      operation_content='获取宿主机列表', remark='')

        try:
            queryset = HostManager().filter_hosts_queryset(group_id=group_id)
        except ComputeError as e:
            return self.exception_response(e)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, context={'mem_unit': mem_unit}, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, context={'mem_unit': mem_unit}, many=True)
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


class VlanViewSet(CustomGenericViewSet):
    """
    vlan类视图
    """
    permission_classes = [IsAuthenticated, ]
    pagination_class = LimitOffsetPagination
    lookup_field = 'id'

    @swagger_auto_schema(
        operation_summary='获取网段列表',
        manual_parameters=[
            openapi.Parameter(
                name='center_id', in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='数据中心id'
            ),
            openapi.Parameter(
                name='group_id', in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='宿主机组id'
            ),
            openapi.Parameter(
                name='public', in_=openapi.IN_QUERY,
                type=openapi.TYPE_BOOLEAN,
                required=False,
                description='筛选条件；true(公网)，false(私网)'
            ),
            openapi.Parameter(
                name='available', in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description='筛选条件，查询有权限使用的vlan；参数不需要值，提交此参数即有效'
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        """
        获取网段列表

            200: {
                  "count": 1,
                  "next": null,
                  "previous": null,
                  "results": [
                    {
                      "id": 1,
                      "name": "private_10.107.50.x",
                      "br": "br_107",
                      "tag": 0,
                      "enable": true,
                      "subnet_ip": "10.107.50.0",
                      "net_mask": "255.255.255.0",
                      "gateway": "10.107.50.254",
                      "dns_server": "159.226.91.150",
                      "subnet_ip_v6": "16a0:10:ab00:1e::",
                      "net_mask_v6": "ffff:ffff:ffff:ffff::",
                      "gateway_v6": "16a0:10:ab00:1e::1",
                      "dns_server_v6": "2001:4860:4860::8888",
                      "remarks": ""
                    }
                  ]
                }
        """
        center_id = request.query_params.get('center_id', None)
        group_id = request.query_params.get('group_id', None)
        query_public = request.query_params.get('public', None)
        available = request.query_params.get('available', None)

        if center_id:
            center_id = str_to_int_or_default(center_id, 0)
            if center_id <= 0:
                exc = exceptions.BadRequestError(msg='query参数center_id无效')
                return self.exception_response(exc)

        if group_id:
            group_id = str_to_int_or_default(group_id, 0)
            if group_id <= 0:
                exc = exceptions.BadRequestError(msg='query参数group_id无效')
                return self.exception_response(exc)

        public = None
        if query_public is not None:
            query_public = query_public.lower()
            if query_public == 'true':
                public = True
            elif query_public == 'false':
                public = False
            else:
                exc = exceptions.BadRequestError(msg='query参数public无效')
                return self.exception_response(exc)

        if available is not None:
            user = request.user
        else:
            user = None

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VLAN, action_flag=LogRecord.SELECT,
                                      operation_content='获取网段列表', remark='')

        queryset = VlanManager().filter_vlan_queryset(center=center_id, group=group_id, is_public=public, user=user)
        queryset = VlanManager().shield_vlan(queryset=queryset, user=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary='查询网段信息'
    )
    def retrieve(self, request, *args, **kwargs):
        """
        查询网段信息

            200：{
                  "id": 1,
                  "name": "private_10.107.50.x",
                  "br": "br_107",
                  "tag": 0,
                  "enable": true,
                  "subnet_ip": "10.107.50.0",
                  "net_mask": "255.255.255.0",
                  "gateway": "10.107.50.254",
                  "dns_server": "159.226.91.150",
                  "subnet_ip_v6": "16a0:10:ab00:1e::",
                  "net_mask_v6": "ffff:ffff:ffff:ffff::",
                  "gateway_v6": "16a0:10:ab00:1e::1",
                  "dns_server_v6": "2001:4860:4860::8888",
                  "remarks": "测试"
                }
            400:{
                  "code": 400,
                  "err_code": "BadRequest",
                  "code_text": "Invalid param \"id\""
                }
            404:{
                  "code": 404,
                  "err_code": "NotFound",
                  "code_text": "Target not found."
                }
        """
        v_id = str_to_int_or_default(kwargs.get(self.lookup_field), None)
        if not v_id:
            exc = exceptions.BadRequestError(msg='Invalid param "id"')
            return Response(exc.data(), status=exc.code)

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VLAN, action_flag=LogRecord.SELECT,
                                      operation_content='查询网段信息', remark='')

        try:
            vlan = VlanManager().get_vlan_by_id(vlan_id=v_id, user=request.user)
        except exceptions.NetworkError as e:
            return Response(e.data(), status=e.code)

        if vlan is None:
            exc = exceptions.NotFoundError()
            return Response(exc.data(), status=exc.code)

        serializer = self.get_serializer(vlan)
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


class ImageViewSet(CustomGenericViewSet):
    """
    镜像类视图
    """
    permission_classes = [IsAuthenticated, ]
    pagination_class = LimitOffsetPagination
    lookup_field = 'id'

    @swagger_auto_schema(
        operation_summary='获取系统镜像列表',
        manual_parameters=[
            openapi.Parameter(
                name='center_id', in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='所属数据中心id'
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
                description="关键字查询(名称和描述)",
                required=False
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        """
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
            系统发行版本: [
                [1,"Windows Desktop"],
                [2,"Windows Server"],
                [3,"Ubuntu"],
                [4,"Fedora"],
                [5,"Centos"],
                [6,"Unknown"]
            ]
            系统发行编号（64字符）：{win10,win11,2021,2019,2204,2004,36,37,7,8,9,....}
            系统架构: [
                [1,"x86-64"],
                [2,"i386"],
                [3,"arm-64"],
                [4,"unknown"]
            ]

            http code 200:
            {
              "count": 2,
              "next": null,
              "previous": null,
              "results": [
                {
                  "id": 1,
                  "name": "centos8-hadoop",
                  "tag": {
                    "id": 0,
                    "name": "基础镜像"
                  },
                  "sys_type": {
                    "id": 2,
                    "name": "Linux"
                  },
                  "release": {
                    "id": 5,
                    "name": "Centos"
                  },
                  "version": "8",
                  "architecture": {
                    "id": 1,
                    "name": "x86-64"
                  },
                  "enable": true,
                  "create_time": "2020-03-06T14:46:27.149648+08:00",
                  "desc": "centos8",
                  "default_user": "root",
                  "default_password": "cnic.cn",
                  "size": 100
                }
              ]
            }
        """
        center_id = str_to_int_or_default(request.query_params.get('center_id', 0), 0)
        tag = str_to_int_or_default(request.query_params.get('tag', 0), 0)
        sys_type = str_to_int_or_default(request.query_params.get('sys_type', 0), 0)
        search = request.query_params.get('search', None)

        try:
            queryset = ImageManager().filter_image_queryset(center_id=center_id, sys_type=sys_type, tag=tag,
                                                            search=search, all_no_filters=True).filter(enable=True)
        except exceptions.ImageError as e:
            exc = exceptions.BadRequestError(msg=str(e))
            return self.exception_response(exc)
        except Exception as e:
            exc = exceptions.Error(msg=str(e))
            return self.exception_response(exc)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({'results': serializer.data})

    @swagger_auto_schema(
        operation_summary='查询系统镜像'
    )
    def retrieve(self, request, *args, **kwargs):
        """
        查询系统镜像

            http code 200:
            {
              "id": 1,
              "name": "centos8-hadoop",
              "tag": {
                "id": 0,
                "name": "基础镜像"
              },
              "sys_type": {
                "id": 2,
                "name": "Linux"
              },
              "release": {
                "id": 5,
                "name": "Centos"
              },
              "version": "8",
              "architecture": {
                "id": 1,
                "name": "x86-64"
              },
              "enable": true,
              "create_time": "2020-03-06T14:46:27.149648+08:00",
              "desc": "centos8",
              "default_user": "root",
              "default_password": "cnic.cn",
              "size": 100
            }
            http code 400, 404:
            {
              "code": 400,
              "err_code": "BadRequest", # NoSuchImage
              "code_text": "镜像id无效"
            }
        """
        image_id = kwargs.get(self.lookup_field)
        image_id = str_to_int_or_default(image_id, None)
        if image_id is None:
            return self.exception_response(exceptions.BadRequestError(msg='镜像id无效'))

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.IMAGE, action_flag=LogRecord.SELECT,
                                      operation_content='查询系统镜像', remark='')

        try:
            image = ImageManager().get_image_by_id(image_id=image_id)
        except exceptions.Error as exc:
            return self.exception_response(exc)

        if image is None:
            return self.exception_response(exceptions.NoSuchImage())

        serializer = self.get_serializer(image)
        return Response(data=serializer.data)

    @swagger_auto_schema(
        operation_summary='修改镜像备注信息',
        request_body=no_body,
        manual_parameters=[
            openapi.Parameter(
                name='remark',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=True,
                description='镜像备注信息'
            )
        ],
        responses={
            200: """
                {
                    'code': 200,
                    'code_text': '修改镜像备注信息成功'
                }
                """,
            "400, 403, 500": """
                    {
                        'code': xxx,
                        'code_text': 'xxx',
                        "err_code": "xxx"
                    }
                    """
        }
    )
    @action(methods=['patch'], url_path='remark', detail=True, url_name='image-remark')
    def vm_remark(self, request, *args, **kwargs):
        """
        修改镜像备注信息
        """
        remark = request.query_params.get('remark', None)
        if remark is None:
            exc = exceptions.BadRequestError(msg='参数有误，无效的备注信息')
            return self.exception_response(exc)

        image_id = kwargs.get(self.lookup_field)
        image_id = str_to_int_or_default(image_id, None)
        if image_id is None:
            return self.exception_response(exceptions.BadRequestError(msg='镜像id无效'))

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.IMAGE, action_flag=LogRecord.SELECT,
                                      operation_content='修改镜像备注信息', remark='')

        try:
            image = ImageManager().get_image_by_id(image_id=image_id)
            if not image:
                raise exceptions.BadRequestError(msg='镜像id无效')
            image.desc = remark
            image.save()
        except exceptions.Error as exc:
            return self.exception_response(exc)

        return Response(data={'code': 200, 'code_text': '修改虚拟机备注信息成功'})

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
    """
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
    """

    @staticmethod
    def get(request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            token, created = Token.objects.get_or_create(user=user)
            slr = serializers.AuthTokenDumpSerializer(token)
            return Response({'token': slr.data})

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.USER, action_flag=LogRecord.SELECT,
                                      operation_content='获取当前用户的token', remark='')

        exc = exceptions.AccessDeniedError(msg='您没有访问权限')
        return Response(data=exc.data(), status=exc.status_code)

    @swagger_auto_schema(
        operation_summary='刷新当前用户的token',
        responses={
            200: """
            {
                "token": {
                    "key": "655e0bcc7216d0ccf7d2be7466f94fa241dc32cb",
                    "user": "username",
                    "created": "2020-03-06T14:46:27.149648+08:00"
                }
            }
            """
        }
    )
    def put(self, request, *args, **kwargs):
        """
        刷新当前用户的token，旧token失效，需要通过身份认证权限
        """

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.USER, action_flag=LogRecord.CHANGE,
                                      operation_content='刷新当前用户的token', remark='')

        user = request.user
        if user.is_authenticated:
            token, created = Token.objects.get_or_create(user=user)
            if not created:
                token.delete()
                token.key = token.generate_key()
                token.save()
            slr = serializers.AuthTokenDumpSerializer(token)
            return Response({'token': slr.data})

        exc = exceptions.AccessDeniedError(msg='您没有访问权限')
        return Response(data=exc.data(), status=exc.status_code)

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
            200: """
                {
                    "token": {
                        "key": "655e0bcc7216d0ccf7d2be7466f94fa241dc32cb",
                        "user": "username",
                        "created": "2020-03-06T14:46:27.149648+08:00"
                    }
                }
            """
        }
    )
    def post(self, request, *args, **kwargs):
        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.USER, action_flag=LogRecord.SELECT,
                                      operation_content='身份验证获取一个token', remark='')

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
    """
    JWT登录认证视图
    """

    @swagger_auto_schema(
        operation_summary='登录认证，获取JWT',
        responses={
            200: """
                {
                  "refresh": "xxx",     # refresh JWT, 此JWT通过刷新API可以获取新的access JWT
                  "access": "xxx"       # access JWT, 用于身份认证，如 'Authorization Bearer accessJWT'
                }
            """
        }
    )
    def post(self, request, *args, **kwargs):
        """
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
        """
        return super().post(request, args, kwargs)


class JWTRefreshView(TokenRefreshView):
    """
    Refresh JWT视图
    """

    @swagger_auto_schema(
        operation_summary='刷新access JWT',
        responses={
            200: """
                {
                  "access": "xxx"
                }
            """
        }
    )
    def post(self, request, *args, **kwargs):
        """
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
        """
        return super().post(request, args, kwargs)


class JWTVerifyView(TokenVerifyView):
    """
    校验access JWT视图
    """

    @swagger_auto_schema(
        operation_summary='校验access JWT是否有效',
        responses={
            200: """{ }"""
        }
    )
    def post(self, request, *args, **kwargs):
        """
        校验access JWT是否有效

            http 200:
            {
            }
            http 401:
            {
              "detail": "Token is invalid or expired",
              "code": "token_not_valid"
            }
        """
        return super().post(request, args, kwargs)


class VDiskViewSet(CustomGenericViewSet):
    """
    虚拟硬盘类视图
    """
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
                description='所属数据中心id'
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
        """
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
                    "ipv4": "10.107.50.252",
                    "ipv6": null
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
        """
        center_id = int(request.query_params.get('center_id', 0))
        group_id = int(request.query_params.get('group_id', 0))
        quota_id = int(request.query_params.get('quota_id', 0))
        user_id = int(request.query_params.get('user_id', 0))
        search = request.query_params.get('search', '')
        mounted = request.query_params.get('mounted', '')

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMDISK, action_flag=LogRecord.SELECT,
                                      operation_content='获取云硬盘列表', remark='')

        user = request.user
        manager = VdiskManager()
        try:
            if user.is_superuser:  # 当前是超级用户，user_id查询参数有效
                queryset = manager.filter_vdisk_queryset(center_id=center_id, group_id=group_id, quota_id=quota_id,
                                                         search=search, user_id=user_id, all_no_filters=True)
            else:
                queryset = manager.filter_vdisk_queryset(center_id=center_id, group_id=group_id, quota_id=quota_id,
                                                         search=search, user_id=user.id)
        except VdiskError as e:
            e.msg = f'查询云硬盘时错误, {str(e)}'
            return self.exception_response(e)

        if mounted == 'true':
            queryset = queryset.filter(vm__isnull=False).all()
        elif mounted == 'false':
            queryset = queryset.filter(vm__isnull=True).all()

        try:
            page = self.paginate_queryset(queryset)
        except Exception as e:
            exc = exceptions.VdiskError(msg=f'查询云硬盘时错误, {str(e)}')
            return self.exception_response(exc)

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
            200: """"""
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
                    "ipv4": "10.107.50.15",
                    "ipv6": null,
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

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMDISK, action_flag=LogRecord.SELECT,
                                      operation_content='查询云主机机可挂载的云硬盘', remark='')

        mgr = VmManager()
        try:
            vm = mgr.get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=('host', 'host__group', 'image'))
        except VmError as e:
            e.msg = f'查询虚拟机错误，{str(e)}'
            return self.exception_response(e)

        if not vm:
            exc = exceptions.VmNotExistError(msg='虚拟机不存在')
            return self.exception_response(exc)

        # 搁置虚拟机，不允许
        status_bool = vm_normal_status(vm=vm)
        if status_bool is False:
            return self.exception_response(exceptions.VmAccessDeniedError(msg='虚拟机搁置状态， 拒绝此操作'))

        center_id = vm.host.group.center_id
        user = request.user

        disk_manager = VdiskManager()
        related_fields = ('user', 'quota', 'quota__group')
        try:
            if user.is_superuser:
                queryset = disk_manager.filter_vdisk_queryset(center_id=center_id, related_fields=related_fields)
            else:
                queryset = disk_manager.filter_vdisk_queryset(center_id=center_id, user_id=user.id,
                                                              related_fields=related_fields)
        except VdiskError as e:
            e.msg = f'查询硬盘列表时错误，{str(e)}'
            return self.exception_response(e)

        try:
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        except Exception as e:
            exc = exceptions.VdiskError(msg=f'查询硬盘列表时错误，{str(e)}')
            return self.exception_response(exc)

    @swagger_auto_schema(
        operation_summary='创建云硬盘',
        responses={
            201: """"""
        }
    )
    def create(self, request, *args, **kwargs):
        """
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

            http code 400, 403, 409, 500：
            {
              "code": xxx,
              "code_text": "xxx",
              "err_code": "Vdiskxxx",   # 错误码
              "data":{ }            # 请求时提交的数据
            }
        """
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid(raise_exception=False):
            code_text = serializer_error_msg(errors=serializer.errors, default='参数验证有误')
            exc = exceptions.VdiskInvalidParams(msg=code_text)
            data = exc.data()
            data['data'] = serializer.data
            return Response(data, status=exc.status_code)

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMDISK, action_flag=LogRecord.ADDITION,
                                      operation_content='创建云硬盘', remark='')

        data = serializer.validated_data
        size = data.get('size')
        center_id = data.get('center_id', None)
        group_id = data.get('group_id', None)
        quota_id = data.get('quota_id', None)
        remarks = data.get('remarks', '')

        manager = VdiskManager()
        try:
            disk = manager.create_vdisk(size=size, user=request.user, center=center_id,
                                        group=group_id, quota=quota_id, remarks=remarks)
        except VdiskError as e:
            r_data = e.data()
            r_data['data'] = data
            return Response(data=r_data, status=e.status_code)

        data = {
            'code': 201,
            'code_text': '创建成功',
            'disk': serializers.VdiskSerializer(instance=disk).data,
        }
        return Response(data=data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        """
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
                "dev": vdb,
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
        """
        disk_uuid = kwargs.get(self.lookup_field, '')

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMDISK, action_flag=LogRecord.SELECT,
                                      operation_content='获取硬盘详细数据', remark='')

        try:
            disk = VdiskManager().get_vdisk_by_uuid(uuid=disk_uuid)
        except VdiskError as e:
            return self.exception_response(e)

        if not disk:
            exc = exceptions.VdiskNotExist()
            return self.exception_response(exc)
        if not disk.user_has_perms(user=request.user):
            exc = exceptions.VdiskAccessDenied(msg='没有权限访问此云硬盘')
            return self.exception_response(exc)

        return Response(data={
            'code': 200,
            'code_text': '获取云硬盘信息成功',
            'vm': self.get_serializer(disk).data
        })

    def destroy(self, request, *args, **kwargs):
        """
        销毁硬盘

            销毁硬盘

            http code 204: 销毁成功
            http code 400, 403, 404, 500: 销毁失败
            {
                "code": xxx,
                "code_text": "xxx",
                "err_code": "xxx",   # 错误码
            }
        """
        disk_uuid = kwargs.get(self.lookup_field, '')

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMDISK, action_flag=LogRecord.DELETION,
                                      operation_content='销毁硬盘', remark='')

        api = VdiskManager()
        try:
            vdisk = api.get_vdisk_by_uuid(uuid=disk_uuid)
        except VdiskError as e:
            e.msg = f'查询硬盘时错误，{str(e)}'
            return self.exception_response(e)

        if vdisk is None:
            return self.exception_response(exceptions.VdiskNotExist())

        if not vdisk.user_has_perms(user=request.user):
            exc = exceptions.VdiskAccessDenied(msg='没有权限访问此硬盘')
            return self.exception_response(exc)

        # 搁置虚拟机，不允许
        status_bool = vm_normal_status(vm=vdisk.vm)
        if status_bool is False:
            return self.exception_response(exceptions.VmAccessDeniedError(msg='虚拟机搁置状态， 拒绝此操作'))

        if vdisk.is_mounted:
            exc = exceptions.VdiskAlreadyMounted(msg='硬盘已被挂载使用，请先卸载后再删除')
            return self.exception_response(exc)

        if not vdisk.soft_delete():
            exc = exceptions.VdiskError(msg='删除硬盘失败，数据库错误')
            return self.exception_response(exc)

        try:
            vdisk.rename_disk_rbd_name()  # 修改ceph rbd名称为删除格式的名称
        except exceptions.VdiskError as e:
            pass

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
            200: """
                {
                    "code": 200,
                    "code_text": "挂载硬盘成功"
                }
            """
        }
    )
    @action(methods=['patch'], url_path='mount', detail=True, url_name='disk-mount')
    def disk_mount(self, request, *args, **kwargs):
        """
        挂载硬盘

            http code 200:
            {
                "code": 200,
                "code_text": "挂载硬盘成功"
            }
            http code 400, 403, 404, 409, 500:
            {
                "code": xxx,
                "code_text": "挂载硬盘失败，xxx",
                "err_code": "xxx"
            }
        """
        disk_uuid = kwargs.get(self.lookup_field, '')
        vm_uuid = request.query_params.get('vm_uuid', '')

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMDISK, action_flag=LogRecord.MOUNT,
                                      operation_content='挂载硬盘', remark='')

        api = VmAPI()
        try:
            api.mount_disk(user=request.user, vm_uuid=vm_uuid, vdisk_uuid=disk_uuid)
        except exceptions.Error as e:
            e.msg = f'挂载硬盘失败，{str(e)}'
            return self.exception_response(e)

        return Response(data={'code': 200, 'code_text': '挂载硬盘成功'})

    @swagger_auto_schema(
        operation_summary='卸载硬盘',
        request_body=no_body,
        responses={
            200: """
                {
                    "code": 200,
                    "code_text": "卸载硬盘成功"
                }
            """
        }
    )
    @action(methods=['patch'], url_path='umount', detail=True, url_name='disk-umount')
    def disk_umount(self, request, *args, **kwargs):
        """
        卸载硬盘

            http code 200:
            {
                "code": 200,
                "code_text": "卸载硬盘成功"
            }
            http code 400, 401, 403, 404, 409, 500:
            {
                "code": xxx,
                "code_text": "卸载硬盘失败，xxx",
                "err_code": "xxx"
            }
        """
        disk_uuid = kwargs.get(self.lookup_field, '')

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMDISK, action_flag=LogRecord.UNMOUNT,
                                      operation_content='卸载硬盘', remark='')

        api = VmAPI()
        try:
            api.umount_disk(user=request.user, vdisk_uuid=disk_uuid)
        except VmError as e:
            return self.exception_response(e)

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
            200: """
                {
                    "code": 200,
                    "code_text": "修改硬盘备注信息成功"
                }
            """
        }
    )
    @action(methods=['patch'], url_path='remark', detail=True, url_name='disk-remark')
    def disk_remark(self, request, *args, **kwargs):
        """
        修改云硬盘备注信息

            http code: 400, 403, 404, 500:
            {
                "code": xxx,
                "code_text": "xxx",
                "err_code": "xxx"
            }
        """
        remark = request.query_params.get('remark', None)
        if remark is None:
            exc = exceptions.BadRequestError(msg='参数有误，未提交remark参数')
            return self.exception_response(exc)

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VMDISK, action_flag=LogRecord.CHANGE,
                                      operation_content='修改云硬盘备注信息', remark='')

        vm_uuid = kwargs.get(self.lookup_field, '')
        api = VdiskManager()
        try:
            api.modify_vdisk_remarks(user=request.user, uuid=vm_uuid, remarks=remark)
        except api.VdiskError as e:
            e.msg = f'修改硬盘备注信息失败，{str(e)}'
            return self.exception_response(e)

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


class QuotaViewSet(CustomGenericViewSet):
    """
    硬盘存储池配额类视图
    """
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
            ),
            openapi.Parameter(
                name='enable',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_BOOLEAN,
                required=False,
                description='True 列出可用的存储池'
            )
        ],
    )
    def list(self, request, *args, **kwargs):
        """
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
                    "name": "vm1",
                    "enable": true
                  },
                  "ceph": {
                    "id": 1,
                    "name": "对象存储集群"
                  },
                  "group": {
                    "id": 1,
                    "name": "宿主机组1"
                  }
                "enable": true,
                "total": 100000,    # 总容量
                "size_used": 30,    # 已用容量
                "max_vdisk": 200    # 硬盘最大容量上限
              ]
            }
        """
        group_id = int(request.query_params.get('group_id', 0))
        enable_bool = request.query_params.get('enable', 'false')  # str
        manager = VdiskManager()

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.ASSETS, action_flag=LogRecord.SELECT,
                                      operation_content='获取硬盘储存池配额列表', remark='')

        if group_id > 0:
            queryset = manager.get_quota_queryset_by_group(group=group_id)
        else:
            queryset = manager.get_quota_queryset()
            queryset = queryset.select_related('cephpool', 'cephpool__ceph', 'group').all()

        if enable_bool == 'true':
            queryset = queryset.filter(enable=True).all()

        try:
            page = self.paginate_queryset(queryset)
        except Exception as e:
            exc = exceptions.Error.from_error(e)
            return self.exception_response(exc)

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


class StatCenterViewSet(CustomGenericViewSet):
    """
    资源统计类视图
    """
    permission_classes = [IsAuthenticated, IsSuperUser]
    pagination_class = None
    lookup_field = 'id'

    @swagger_auto_schema(
        operation_summary='获取所有资源统计信息',
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
        获取所有资源统计信息列表

            http code 200:
            {
              "code": 200,
              "code_text": "get ok",
              "centers": [
                {
                  "id": 1,
                  "name": "怀柔数据中心",
                  "mem_total": 165536,
                  "mem_allocated": 15360,
                  "vcpu_total": 54,
                  "vcpu_allocated": 24,
                  "vm_created": 6
                }
              ],
              "groups": [
                {
                  "id": 1,
                  "name": "宿主机组1",
                  "center__name": "怀柔数据中心",
                  "mem_total": 132768,
                  "mem_allocated": 15360,
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
                  "vcpu_total": 24,
                  "vcpu_allocated": 24,
                  "vm_created": 6
                }
              ]
            }
        """
        mem_unit = str.upper(request.query_params.get('mem_unit', 'UNKNOWN'))
        if mem_unit not in ['GB', 'MB', 'UNKNOWN']:
            exc = exceptions.BadRequestError(msg='无效的内存单位, 正确格式为GB、MB或为空')
            return self.exception_response(exc)

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.ASSETS, action_flag=LogRecord.SELECT,
                                      operation_content='获取所有资源统计信息', remark='')

        centers = CenterManager().get_stat_center_queryset().values(
            'id', 'name', 'mem_total', 'mem_allocated', 'vcpu_total', 'vcpu_allocated', 'vm_created')
        groups = GroupManager().get_stat_group_queryset().values(
            'id', 'name', 'center__name', 'mem_total', 'mem_allocated',
            'vcpu_total', 'vcpu_allocated', 'vm_created')
        hosts = Host.objects.select_related('group').values(
            'id', 'ipv4', 'group__name', 'mem_total', 'mem_allocated',
            'vcpu_total', 'vcpu_allocated', 'vm_created').all()

        for objs in [centers, groups, hosts]:
            for item in objs:
                if mem_unit in ['MB', 'UNKNOWN']:
                    item['mem_total'] = item['mem_total'] * 1024
                    item['mem_allocated'] = item['mem_allocated'] * 1024
                    item['mem_unit'] = 'MB'
                else:
                    item['mem_unit'] = 'GB'
        return Response(data={'code': 200, 'code_text': 'get ok', 'centers': centers, 'groups': groups, 'hosts': hosts})

    @swagger_auto_schema(
        operation_summary='获取一个数据中心的资源统计信息',
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
    @action(methods=['get'], detail=True, url_path='center', url_name='center-stat')
    def center_stat(self, request, *args, **kwargs):
        """
        获取一个数据中心的资源统计信息列表

            http code 200:
            {
              "code": 200,
              "code_text": "get ok",
              "center": {
                  "id": 1,
                  "name": "怀柔数据中心",
                  "mem_total": 165536,
                  "mem_allocated": 15360,
                  "vcpu_total": 54,
                  "vcpu_allocated": 24,
                  "vm_created": 6
                },
              "groups": [
                {
                  "id": 1,
                  "name": "宿主机组1",
                  "center__name": "怀柔数据中心",
                  "mem_total": 132768,
                  "mem_allocated": 15360,
                  "vcpu_total": 24,
                  "vcpu_allocated": 24,
                  "vm_created": 6
                }
              ]
            }
        """
        mem_unit = str.upper(request.query_params.get('mem_unit', 'UNKNOWN'))
        if mem_unit not in ['GB', 'MB', 'UNKNOWN']:
            exc = exceptions.BadRequestError(msg='无效的内存单位, 正确格式为GB、MB或为空')
            return self.exception_response(exc)

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.ASSETS, action_flag=LogRecord.SELECT,
                                      operation_content='获取一个数据中心的资源统计信息', remark='')

        c_id = str_to_int_or_default(kwargs.get(self.lookup_field, 0), 0)
        if c_id > 0:
            center = CenterManager().get_stat_center_queryset(filters={'id': c_id}).values(
                'id', 'name', 'mem_total', 'mem_allocated', 'vcpu_total',
                'vcpu_allocated', 'vm_created').first()
        else:
            center = None

        if not center:
            exc = exceptions.NotFoundError(msg='数据中心不存在')
            return self.exception_response(exc)

        groups = GroupManager().get_stat_group_queryset(filters={'center': c_id}).values(
            'id', 'name', 'center__name', 'mem_total', 'mem_allocated',
            'vcpu_total', 'vcpu_allocated', 'vm_created')

        for objs in [[center], groups]:
            for item in objs:
                if mem_unit in ['MB', 'UNKNOWN']:
                    item['mem_total'] = item['mem_total'] * 1024
                    item['mem_allocated'] = item['mem_allocated'] * 1024
                    item['mem_unit'] = 'MB'
                else:
                    item['mem_unit'] = 'GB'

        return Response(data={'code': 200, 'code_text': 'get ok', 'center': center, 'groups': groups})

    @swagger_auto_schema(
        operation_summary='获取一个机组的资源统计信息',
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
    @action(methods=['get'], detail=True, url_path='group', url_name='group-stat')
    def group_stat(self, request, *args, **kwargs):
        """
        获取一个机组的资源统计信息列表

            http code 200:
            {
              "code": 200,
              "code_text": "get ok",
              "group": {
                  "id": 1,
                  "name": "宿主机组1",
                  "center__name": "怀柔数据中心",
                  "mem_total": 132768,
                  "mem_allocated": 15360,
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
                  "vcpu_total": 24,
                  "vcpu_allocated": 24,
                  "vm_created": 6
                }
              ]
            }
        """
        mem_unit = str.upper(request.query_params.get('mem_unit', 'UNKNOWN'))
        if mem_unit not in ['GB', 'MB', 'UNKNOWN']:
            exc = exceptions.BadRequestError(msg='无效的内存单位, 正确格式为GB、MB或为空')
            return self.exception_response(exc)

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.ASSETS, action_flag=LogRecord.SELECT,
                                      operation_content='获取一个机组的资源统计信息', remark='')

        g_id = str_to_int_or_default(kwargs.get(self.lookup_field, 0), 0)
        if g_id > 0:
            group = GroupManager().get_stat_group_queryset(filters={'id': g_id}).values(
                'id', 'name', 'center__name', 'mem_total', 'mem_allocated',
                'vcpu_total', 'vcpu_allocated', 'vm_created').first()
        else:
            group = None

        if not group:
            exc = exceptions.NotFoundError(msg='机组不存在')
            return self.exception_response(exc)

        hosts = Host.objects.select_related('group').filter(group=g_id).values(
            'id', 'ipv4', 'group__name', 'mem_total', 'mem_allocated',
            'vcpu_total', 'vcpu_allocated', 'vm_created').all()

        for objs in [[group], hosts]:
            for item in objs:
                if mem_unit in ['MB', 'UNKNOWN']:
                    item['mem_total'] = item['mem_total'] * 1024
                    item['mem_allocated'] = item['mem_allocated'] * 1024
                    item['mem_unit'] = 'MB'
                else:
                    item['mem_unit'] = 'GB'
        return Response(data={'code': 200, 'code_text': 'get ok', 'group': group, 'hosts': hosts})

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        Defaults to using `self.serializer_class`.
        Custom serializer_class
        """
        return Serializer


class PCIDeviceViewSet(CustomGenericViewSet):
    """
    PCI设备类视图
    """
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
                description='筛选条件，所属数据中心id'
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
        """
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
        """
        center_id = str_to_int_or_default(request.query_params.get('center_id', 0), 0)
        group_id = str_to_int_or_default(request.query_params.get('group_id', 0), 0)
        host_id = str_to_int_or_default(request.query_params.get('host_id', 0), 0)
        type_val = str_to_int_or_default(request.query_params.get('type', 0), 0)
        search = str_to_int_or_default(request.query_params.get('search', 0), 0)

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.ASSETS, action_flag=LogRecord.SELECT,
                                      operation_content='获取PCI设备列表', remark='')

        user = request.user
        if not (user and user.is_authenticated):
            exc = exceptions.AuthenticationFailedError(msg='未身份认证，无权限')
            return self.exception_response(exc)

        try:
            queryset = PCIDeviceManager().filter_pci_queryset(
                center_id=center_id, group_id=group_id, host_id=host_id,
                type_id=type_val, search=search, user=user, related_fields=('host', 'vm'))
        except DeviceError as e:
            return self.exception_response(e)

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
                    "ipv4": "10.107.50.15",
                    "ipv6": "16a0:10:ab00:1e::102"
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
            http code 400, 404, 500:
            {
                "code": xxx,
                "code_text": "xxx",
                "err_code": "xxx"
            }
        """
        vm_uuid = kwargs.get('vm_uuid', '')

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.ASSETS, action_flag=LogRecord.SELECT,
                                      operation_content='查询主机可挂载的PCI设备', remark='')

        try:
            vm = VmManager().get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=('host',))
        except VmError as e:
            return self.exception_response(e)

        if not vm:
            return self.exception_response(exceptions.VmNotExistError(msg='虚拟机不存在'))

        status_bool = vm_normal_status(vm=vm)
        if status_bool is False:
            return self.exception_response(exceptions.VmAccessDeniedError(msg='虚拟机搁置状态， 拒绝此操作'))

        try:
            queryset = PCIDeviceManager().get_pci_queryset_by_host(host=vm.host)
            queryset = queryset.select_related('host', 'vm').all()
        except DeviceError as e:
            return self.exception_response(e)

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
        """
        挂载PCI设备

            http code 201:
            {
                "code": 201,
                "code_text": "挂载设备成功"
            }
            http code 400, 404, 409, 500:
            {
                "code": xxx,
                "code_text": "挂载设备失败，xxx",
                "err_code": "xxx"
            }

        """
        dev_id = str_to_int_or_default(kwargs.get(self.lookup_field, 0), 0)
        vm_uuid = request.query_params.get('vm_uuid', '')

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.ASSETS, action_flag=LogRecord.MOUNT,
                                      operation_content='挂载PCI设备', remark='')

        if dev_id <= 0:
            exc = exceptions.BadRequestError(msg='无效的设备ID')
            return self.exception_response(exc)
        if not vm_uuid:
            exc = exceptions.BadRequestError(msg='无效的虚拟机ID')
            return self.exception_response(exc)

        try:
            VmAPI().mount_pci_device(vm_uuid=vm_uuid, device_id=dev_id, user=request.user)
        except VmError as e:
            e.msg = f'挂载失败，{str(e)}'
            return self.exception_response(e)

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
        """
        卸载PCI设备

            http code 201:
            {
                "code": 201,
                "code_text": "卸载设备成功"
            }
            http code 400, 403, 404, 409, 500:
            {
                "code": xxx,
                "code_text": "卸载设备失败，xxx",
                "err_code": "xxx"
            }

        """
        dev_id = str_to_int_or_default(kwargs.get(self.lookup_field, 0), 0)
        if dev_id <= 0:
            exc = exceptions.BadRequestError(msg='无效的设备ID')
            return self.exception_response(exc)

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.ASSETS, action_flag=LogRecord.UNMOUNT,
                                      operation_content='卸载PCI设备', remark='')

        try:
            VmAPI().umount_pci_device(device_id=dev_id, user=request.user)
        except VmError as exc:
            return self.exception_response(exc)

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


class MacIPViewSet(CustomGenericViewSet):
    permission_classes = [IsAuthenticated, ]
    pagination_class = MacIpLimitOffsetPagination

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
                      "mac": "C8:00:0A:6B:32:FD",
                      "ipv4": "10.107.50.253",
                      "ipv6": "16a0:10:ab00:1e::102",
                      "used": true
                    }
                  ]
                }
        """
        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.ASSETS, action_flag=LogRecord.SELECT,
                                      operation_content='获取MAC IP列表', remark='')

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


class FlavorViewSet(CustomGenericViewSet):
    """
    虚拟机硬件配置样式视图
    """
    permission_classes = [IsAuthenticated, ]
    pagination_class = LimitOffsetPagination

    @swagger_auto_schema(
        operation_summary='列举硬件配置样式',
        request_body=no_body,
        manual_parameters=[
            openapi.Parameter(
                name='mem_unit',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description='内存计算单位（默认MB，可选GB）'
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        """
        获取虚拟机硬件配置样式列表

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
        mem_unit = str.upper(request.query_params.get('mem_unit', 'UNKNOWN'))
        if mem_unit not in ['GB', 'MB', 'UNKNOWN']:
            exc = exceptions.BadRequestError(msg='无效的内存单位, 正确格式为GB、MB或为空')
            return self.exception_response(exc)

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.ASSETS, action_flag=LogRecord.SELECT,
                                      operation_content='列举硬件配置样式', remark='')

        queryset = FlavorManager().get_user_flaver_queryset(user=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, context={'mem_unit': mem_unit}, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, context={'mem_unit': mem_unit}, many=True)
        return Response({'results': serializer.data})

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.FlavorSerializer
        return Serializer


class VPNViewSet(CustomGenericViewSet):
    """
    VPN视图
    """
    permission_classes = [IsAuthenticated, ]
    pagination_class = LimitOffsetPagination
    lookup_field = 'username'
    lookup_value_regex = '[^/]+'  # 匹配排除“/”的任意字符串

    @swagger_auto_schema(
        operation_summary='获取用户vpn信息',
        request_body=no_body,
        responses={
            200: ''
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """
        获取vpn信息

            http code 200:
                {
                  "username": "testuser",
                  "password": "password",
                  "active": true,
                  "create_time": "2020-07-29T15:12:08.715731+08:00",
                  "modified_time": "2020-07-29T15:12:08.715998+08:00"
                }
            http code 404:
                {
                  "err_code": "NoSuchVPN",
                  "code_text": "vpn账户不存在"
                }
        """

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VPN, action_flag=LogRecord.SELECT,
                                      operation_content='获取用户vpn信息', remark='')

        username = kwargs.get(self.lookup_field)
        mgr = VPNManager()
        vpn = mgr.get_vpn(username=username)
        if not vpn:
            return self.exception_response(exceptions.NoSuchVPN())

        serializer = self.get_serializer(vpn)
        return Response(data=serializer.data)

    @swagger_auto_schema(
        operation_summary='创建vpn账户',
        responses={
            201: ''
        }
    )
    def create(self, request, *args, **kwargs):
        """
        创建vpn

            http code 201:
                {
                  "username": "testuser",
                  "password": "password",
                  "active": true,
                  "create_time": "2020-07-29T15:12:08.715731+08:00",
                  "modified_time": "2020-07-29T15:12:08.715998+08:00"
                }
            http code 400:
                {
                  "err_code": "AlreadyExists",
                  "code_text": "用户vpn账户已存在"
                }
            http code 500:
                {
                  "err_code": "InternalServerError",
                  "code_text": "创建用户vpn账户失败"
                }
        """
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid(raise_exception=False):
            msg = serializer_error_msg(serializer.errors, default='请求数据无效')
            exc = exceptions.BadRequestError(msg=msg)
            return self.exception_response(exc)

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VPN, action_flag=LogRecord.ADDITION,
                                      operation_content='创建vpn账户', remark='')

        valid_data = serializer.validated_data
        username = valid_data.get('username')
        password = valid_data.get('password')
        mgr = VPNManager()
        vpn = mgr.get_vpn(username=username)
        if vpn:
            exc = exceptions.VPNAlreadyExists()
            return self.exception_response(exc)

        create_user = request.user.username
        try:
            vpn = mgr.create_vpn(username=username, password=password, remarks=create_user, create_user=create_user,
                                 active=VPN_USER_ACTIVE_DEFAULT)
        except VPNError as e:
            e.msg = f'创建用户vpn账户失败, {e}'
            return self.exception_response(e)

        return Response(data=serializers.VPNSerializer(vpn).data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary='修改vpn账户密码',
        request_body=no_body,
        manual_parameters=[
            openapi.Parameter(
                name='password',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=True,
                description='新密码'
            )
        ],
        responses={
            200: ''
        }
    )
    def partial_update(self, request, *args, **kwargs):
        """
        修改VPN账户密码

            http code 200:
                {
                  "username": "testuser",
                  "password": "password",
                  "active": true,
                  "create_time": "2020-07-29T15:12:08.715731+08:00",
                  "modified_time": "2020-07-29T15:12:08.715998+08:00"
                }
            http code 400:
                {
                  "err_code": "BadRequest",
                  "code_text": "xxx"
                }
            http code 404:
                {
                  "err_code": "NoSuchVPN",
                  "code_text": "vpn账户不存在"
                }
            http code 500:
                {
                  "err_code": "InternalServerError",
                  "code_text": "修改用户vpn密码失败"
                }
        """
        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VPN, action_flag=LogRecord.CHANGE,
                                      operation_content='修改VPN账户密码', remark='')

        username = kwargs.get(self.lookup_field)
        password = request.query_params.get('password')
        if password is None:
            exc = exceptions.BadRequestError(msg='Query param "password" is required.')
            return self.exception_response(exc)

        if not (6 <= len(password) <= 64):
            exc = exceptions.BadRequestError(msg='Password must be 6-64 characters.')
            return self.exception_response(exc)

        mgr = VPNManager()
        vpn = mgr.get_vpn(username=username)
        if not vpn:
            exc = exceptions.NoSuchVPN()
            return Response(data=exc.data(), status=exc.status_code)

        if not vpn.set_password(password, modified_user=request.user.username):
            exc = exceptions.VPNError(msg='修改用户vpn密码失败')
            return self.exception_response(exc)

        return Response(data=serializers.VPNSerializer(vpn).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary='激活vpn账户',
        request_body=no_body,
        responses={
            200: ''
        }
    )
    @action(methods=["post"], detail=True, url_path='active', url_name='active-vpn')
    def active_vpn(self, request, *args, **kwargs):
        """
        激活vpn账户

            http code 200:
                {
                  "username": "testuser",
                  "password": "password",
                  "active": true,
                  "create_time": "2020-07-29T15:12:08.715731+08:00",
                  "modified_time": "2020-07-29T15:12:08.715998+08:00"
                }
            http code 4xx, 5xx:
                {
                  "err_code": "BadRequest",
                  "code_text": "xxx"
                }

            错误码：
                404:
                    NoSuchVPN: vpn账户不存在
                500:
                    InternalServerError: 激活用户vpn失败
        """
        username = kwargs.get(self.lookup_field)

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VPN, action_flag=LogRecord.CHANGE,
                                      operation_content='激活vpn账户', remark='')

        mgr = VPNManager()
        vpn = mgr.get_vpn(username=username)
        if not vpn:
            self.exception_response(exceptions.NoSuchVPN())

        if vpn.active is not True:
            vpn.active = True
            try:
                vpn.save(update_fields=['active', 'modified_time'])
            except Exception as e:
                return self.exception_response(exceptions.VPNError(msg=f'激活用户vpn失败，{str(e)}'))

        return Response(data=serializers.VPNSerializer(vpn).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary='停用vpn账户',
        request_body=no_body,
        responses={
            200: ''
        }
    )
    @action(methods=['post'], url_path='deactive', detail=True, url_name='deactive-vpn')
    def deactive_vpn(self, request, *args, **kwargs):
        """
        停用vpn账户

            http code 200:
                {
                  "username": "testuser",
                  "password": "password",
                  "active": true,
                  "create_time": "2020-07-29T15:12:08.715731+08:00",
                  "modified_time": "2020-07-29T15:12:08.715998+08:00"
                }
            http code 4xx, 5xx:
                {
                  "err_code": "BadRequest",
                  "code_text": "xxx"
                }

            错误码：
                404:
                    NoSuchVPN: vpn账户不存在
                500:
                    InternalServerError: 激活用户vpn失败
        """
        username = kwargs.get(self.lookup_field)

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.VPN, action_flag=LogRecord.CHANGE,
                                      operation_content='停用vpn账户', remark='')

        mgr = VPNManager()
        vpn = mgr.get_vpn(username=username)
        if not vpn:
            self.exception_response(exceptions.NoSuchVPN())

        if vpn.active is not False:
            vpn.active = False
            try:
                vpn.save(update_fields=['active', 'modified_time'])
            except Exception as e:
                return self.exception_response(exceptions.VPNError(msg=f'停用用户vpn失败，{str(e)}'))

        return Response(data=serializers.VPNSerializer(vpn).data, status=status.HTTP_200_OK)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.VPNSerializer
        elif self.action == 'create':
            return serializers.VPNCreateSerializer
        return Serializer


class MigrateTaskViewSet(CustomGenericViewSet):
    permission_classes = [IsAuthenticated, ]
    pagination_class = LimitOffsetPagination
    lookup_field = 'id'
    lookup_value_regex = '.+'

    @swagger_auto_schema(
        operation_summary='查询虚拟机迁移任务状态',
        request_body=no_body
    )
    def retrieve(self, request, *args, **kwargs):
        """
        查询虚拟机迁移任务状态

            >> http code 200:
            {
              "id": 2,
              "vm_uuid": "ede9a97e049949d0a1ef90fe58d7cc39",
              "src_host_id": 4,
              "src_host_ipv4": "10.0.200.83",
              "src_undefined": false,
              "src_is_free": false,
              "dst_host_id": 5,
              "dst_host_ipv4": "10.0.200.80",
              "dst_is_claim": false,
              "migrate_time": "2021-06-15T16:59:38.291440+08:00",
              "migrate_complete_time": null,
              "status": "failed",
              "content": "unsupported configuration: Target CPU check full does not match source partial",
              "tag": "live"
            }
            >> http code 403, 404, 500
            {
                "code": xxx,
                "code_text": "xxx",
                "err_code": "xxx"
            }
        """
        task_id = kwargs.get(self.lookup_field, '')

        # 用户操作日志记录
        user_operation_record.add_log(request=request, type=LogRecord.MIGRATE, action_flag=LogRecord.SELECT,
                                      operation_content='查询云主机迁移任务状态', remark='')

        try:
            task = VmMigrateManager.get_migrate_task(_id=task_id, user=request.user)
        except VmError as exc:
            return self.exception_response(exc)

        if task is None:
            return self.exception_response(exc=exceptions.NotFoundError(msg='迁移任务不存在'))

        serializer = self.get_serializer(task)
        return Response(data=serializer.data)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.MigrateTaskSerializer

        return Serializer


class VersionViewSet(CustomGenericViewSet):
    permission_classes = [IsAuthenticated, ]
    pagination_class = LimitOffsetPagination

    @swagger_auto_schema(
        operation_summary='查询部署版本',
        request_body=no_body
    )
    def list(self, request, *args, **kwargs):
        """
        查询当前部署EVCloud版本
        """
        return Response(data={'version': __version__})

    def get_serializer_class(self):
        """
        Return the class to use for the serializer.
        Defaults to using `self.serializer_class`.
        Custom serializer_class
        """
        return Serializer
