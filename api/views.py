from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.schemas import AutoSchema
from rest_framework.compat import coreapi, coreschema
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.serializers import Serializer
from rest_framework.decorators import action
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from vms.manager import VmManager, VmAPI, VmError
from novnc.manager import NovncTokenManager, NovncError
from compute.models import Center, Group, Host
from compute.managers import HostManager, CenterManager, GroupManager, ComputeError
from network.models import Vlan
from image.managers import ImageManager
from vdisk.models import Vdisk
from vdisk.manager import VdiskManager,VdiskError
from . import serializers
from utils.logs import log_user

# Create your views here.

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
                    name='user_id',
                    location='query',
                    required=False,
                    schema=coreschema.Integer(description='用户id'),
                    description='所属用户，当前为超级用户时此参数有效'
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
            ],
            'vm_sys_snap': [
                coreapi.Field(
                    name='remark',
                    location='query',
                    required=False,
                    schema=coreschema.String(description='备注信息'),
                    description='快照备注信息'
                ),
            ],
            'delete_vm_snap': [
                coreapi.Field(
                    name='id',
                    location='path',
                    required=True,
                    schema=coreschema.String(description='snap id'),
                    description='快照id'
                ),
            ],
            'vm_snap_remark': [
                coreapi.Field(
                    name='remark',
                    location='query',
                    required=True,
                    schema=coreschema.String(description='新的备注信息'),
                    description='快照备注信息'
                ),
            ]
        }
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
            vm = VmManager().get_vm_by_uuid(vm_uuid=vm_uuid)
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

        return Response(data={'code': 200, 'code_text': '获取虚拟机状态成功',
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

    @action(methods=['post'], url_path='snap', detail=True, url_name='vm_sys_snap')
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

    @action(methods=['delete'], url_path=r'snap/(?P<id>[0-9]+)', detail=False, url_name='delete_vm_snap')
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

    @action(methods=['patch'], url_path=r'snap/(?P<id>[0-9]+)/remark', detail=False, url_name='vm_snap_remark')
    def vm_snap_remark(self, request, *args, **kwargs):
        '''
        修改虚拟机快照备注信息
        '''
        remark = request.query_params.get('remark')
        if not remark:
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

    @action(methods=['post'], url_path=r'rollback/(?P<snap_id>[0-9]+)', detail=True, url_name='vm_rollback_snap')
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
            ]
        }
    )

    def list(self, request, *args, **kwargs):
        '''
        获取宿主机组列表

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
                    name='tag',
                    location='query',
                    required=False,
                    schema=coreschema.Integer(description='标签'),
                    description='镜像标签'
                ),
                coreapi.Field(
                    name='sys_type',
                    location='query',
                    required=False,
                    schema=coreschema.Integer(description='系统类型'),
                    description='系统类型'
                ),
                coreapi.Field(
                    name='search',
                    location='query',
                    required=False,
                    schema=coreschema.String(description='关键字查询'),
                    description='关键字查询'
                ),
            ]
        }
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
                  "create_time": "2019-10-15 16:25:26",
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
                                                            search=search, all_no_filters=request.user.is_superuser)
        except Exception as e:
            return Response({'code': 400, 'code_text': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({'results': serializer.data})

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


class JWTObtainPairView(TokenObtainPairView):
    '''
    JWT登录认证视图
    '''
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

    # api docs
    schema = CustomAutoSchema(
        manual_fields={
            'list': [
                coreapi.Field(
                    name='center_id',
                    location='query',
                    required=False,
                    schema=coreschema.Integer(description='分中心id'),
                    description='所属分中心',
                    type='int'
                ),
                coreapi.Field(
                    name='group_id',
                    location='query',
                    required=False,
                    schema=coreschema.Integer(description='机组id'),
                    description='所属机组'
                ),
                coreapi.Field(
                    name='quota_id',
                    location='query',
                    required=False,
                    schema=coreschema.Integer(description='硬盘存储池id'),
                    description='所属硬盘存储池'
                ),
                coreapi.Field(
                    name='user_id',
                    location='query',
                    required=False,
                    schema=coreschema.Integer(description='用户id'),
                    description='所属用户，当前为超级用户时此参数有效'
                ),
                coreapi.Field(
                    name='search',
                    location='query',
                    required=False,
                    schema=coreschema.String(description='查询关键字'),
                    description='查询关键字'
                ),
                coreapi.Field(
                    name='mounted',
                    location='query',
                    required=False,
                    schema=coreschema.Boolean(description='true=已挂载；false=未挂载'),
                    description='是否挂载查询条件'
                ),
            ],
            'disk_mount': [
                coreapi.Field(
                    name='vm_uuid',
                    location='query',
                    required=True,
                    schema=coreschema.String(description='虚拟机uuid'),
                    description='要挂载的虚拟机uuid'
                )
            ],
            'disk_remark': [
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
                  "create_time": "2019-11-13 16:56:20",
                  "attach_time": "2019-11-14 09:11:44",
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
                "create_time": "2019-11-07 11:21:44",
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
                "create_time": "2019-11-07 11:19:55",
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

        try:
            vdisk.deleted = True
            vdisk.save(update_fields=['deleted'])
        except Exception as e:
            return Response(data={'code': 400, 'code_text': f'销毁硬盘失败，{str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['patch'], url_path='mount', detail=True, url_name='disk_mount')
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

    @action(methods=['patch'], url_path='umount', detail=True, url_name='disk_umount')
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

    @action(methods=['patch'], url_path='remark', detail=True, url_name='disk_remark')
    def disk_remark(self, request, *args, **kwargs):
        '''
        修改云硬盘备注信息
        '''
        remark = request.query_params.get('remark')
        if not remark:
            return Response(data={'code': 400, 'code_text': '参数有误，无效的备注信息'}, status=status.HTTP_400_BAD_REQUEST)

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
        if self.action == 'list':
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
            ]
        }
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

    # api docs
    schema = CustomAutoSchema(
        manual_fields={
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
        groups = GroupManager().get_stat_group_wueryset().values('id', 'name', 'center__name', 'mem_total',
                                        'mem_allocated', 'mem_reserved', 'vcpu_total', 'vcpu_allocated', 'vm_created')
        hosts = Host.objects.select_related('group').values('id', 'ipv4', 'group__name', 'mem_total', 'mem_allocated',
                                            'mem_reserved', 'vcpu_total', 'vcpu_allocated', 'vm_created').all()
        return Response(data={'code': 200, 'code_text': 'get ok', 'centers': centers, 'groups': groups, 'hosts': hosts})

    @action(methods=['get'], detail=True, url_path='center', url_name='center_stat')
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
            center = CenterManager().get_stat_center_queryset(filter={'id': c_id}).values('id', 'name', 'mem_total',
                            'mem_allocated','mem_reserved', 'vcpu_total', 'vcpu_allocated', 'vm_created').first()
        else:
            center = None
        if not center:
            return Response({'code': 200, 'code_text': '分中心不存在'}, status=status.HTTP_400_BAD_REQUEST)

        groups = GroupManager().get_stat_group_wueryset(filter={'center': c_id}).values('id', 'name', 'center__name',
                             'mem_total', 'mem_allocated', 'mem_reserved', 'vcpu_total', 'vcpu_allocated', 'vm_created')
        return Response(data={'code': 200, 'code_text': 'get ok', 'center': center, 'groups': groups})

    @action(methods=['get'], detail=True, url_path='group', url_name='group_stat')
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
            group = GroupManager().get_stat_group_wueryset(filter={'id': g_id}).values('id', 'name', 'center__name',
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
