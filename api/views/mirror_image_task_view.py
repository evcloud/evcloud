import os
import subprocess

from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import Serializer
from drf_yasg.utils import swagger_auto_schema, no_body
from drf_yasg import openapi

from api import serializers
from api.views.views import serializer_error_msg
from api.viewsets import CustomGenericViewSet
from image.managers import MirrorImageManager
from image.models import VmXmlTemplate, MirrorImageTask
from logrecord.manager import user_operation_record, extract_string
from utils.permissions import APIIPPermission
from utils import errors as exceptions


class MirrorImageTaskViewSet(CustomGenericViewSet):
    """
    可用资源配额类视图
    """
    permission_classes = [IsAuthenticated, APIIPPermission]
    pagination_class = LimitOffsetPagination

    @swagger_auto_schema(
        operation_summary='获取公共镜像任务',
        manual_parameters=[
            openapi.Parameter(
                name='task_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='任务id',
            ),
            openapi.Parameter(
                name='status',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=False,
                description='任务状态:{1:下载中, 2:下载完成, 3:上传中, 4:上传完成, 5:上传失败, 6:下载失败, 7:无}',
            ),
        ],
        responses={
            200: ''
        }
    )
    def list(self, request, *args, **kwargs):
        """
        查看公共镜像任务

            {
              "id": 1,
              "operate_status": "下载",  # 操作(上传/下载)
              "task_status": "无",    # 任务状态
              "mirrors_image_service_url": "http://223.193.36.121:8001/",  # 公共镜像url
              "bucket_name": "202020",  # 存储桶名称
              "file_path": "develop-iso-test.qcow2",  #镜像路径
              "token": "ad39f5a689ea0b185dfa8a4e7df61a8c31c04d6c",  # 存储桶token
              "mirror_image_name": "devlop-test-centos9",
              "mirror_image_sys_type": "Linux",
              "mirror_image_version": "stream 9",
              "mirror_image_release": "Centos",
              "mirror_image_architecture": "x86-64",
              "mirror_image_boot_mode": "BIOS",
              "mirror_image_base_image": "develop-iso-test.qcow2",
              "mirror_image_enable": false,
              "mirror_image_xml_tpl": 1,  # xml模板
              "mirror_image_default_user": "xxx",  # 镜像默认用户
              "mirror_image_default_password": "xxx",   # 镜像默认密码
              "mirror_image_size": 2,  # 镜像大小
              "user": "wanghuang",
              "desc": null,
              "import_date": null,  # 导入开始时间
              "import_date_complate": null,   # 导入完成时间
              "export_date": null,   # 导出开始时间
              "export_date_complate": null,    # 导出完成时间
              "error_msg": null,   # 错误信息
              "create_time": "2024-07-01T09:09:48.867187+08:00",
              "update_time": "2024-07-01T09:09:48.867261+08:00"
            }

        """

        task_id = request.query_params.get('task_id', None)
        status = request.query_params.get('status', None)

        mirror_image_mamager = MirrorImageManager()

        self.queryset = mirror_image_mamager.get_mirror_image_queryset(task_id=task_id, status=status)

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary='添加公共镜像下载任务信息',
        # request_body=no_body,
        manual_parameters=[
        ],
        responses={
            200: "{'id': 1}"  # 任务id
        }
    )
    @action(methods=['post'], detail=False, url_path=r'image/pull', url_name='image-pull')
    def mirror_image_task_pull(self, request, *args, **kwargs):
        """
        添加公共镜像下载任务

            {
              "mirrors_image_service_url": "string",  # 公共镜像地址  必填
              "bucket_name": "string",  # 存储桶名称 必填  必填
              "file_path": "string",  # 公共镜像路径  必填
              "token": "string",  # 存储桶 token  必填
              "mirror_image_name": "string",  # 镜像名称  必填
              "mirror_image_base_image": "string",  # 导入ceph的镜像名称  必填
              "xml_tpl_search": "Linux"  # xml 名称关键字  如：Linux、hugepage等
              "mirror_image_sys_type": "Linux",  # 系统类型   Windows、Linux、Unix、MacOS、Android、其他
              "mirror_image_version": "stream 9",  # 系统发行编号
              "mirror_image_release": "Centos",  # 系统发行版本  Centos、Ubuntu、Windows Desktop、Windows Server、Fedora、Rocky、Unknown
              "mirror_image_architecture": "x86-64",  # 系统架构  x86-64、i386、arm-64、unknown
              "mirror_image_boot_mode": "BIOS", #系统启动方式  BIOS、UEFI
              "mirror_image_enable": true,  # 镜像启用
              "desc": "string",  # 描述
              "mirror_image_default_user": "xxx",  # 镜像默认用户
              "mirror_image_default_password": "xxx", # 系统默认密码
              "mirror_image_size": 0  # 镜像大小
            }
        """
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid(raise_exception=False):
            msg = serializer_error_msg(serializer.errors, default='请求数据无效')
            exc = exceptions.BadRequestError(msg=msg)
            return self.exception_response(exc)

        valid_data = serializer.validated_data
        mirror_image_mamager = MirrorImageManager()

        vo_or_user = request.query_params.get('_who_action', '')
        username = request.user.username
        real_user = ''
        if vo_or_user:
            vo, real_user = extract_string(text=vo_or_user)

        if real_user:
            valid_data.update({'user': real_user})
        else:
            valid_data.update({'user': username})

        valid_data.update({'operate': 1})
        valid_data.update({'status': 7})
        task_dict = {key: value for key, value in valid_data.items() if value != 'string'}

        hostname = self.get_hostname()
        if hostname:
            task_dict.update({'local_hostname': hostname})

        try:
            obj = mirror_image_mamager.add_mirror_image_pull_task(task_dict=task_dict)
        except Exception as e:
            return self.exception_response(e)

        return Response(status=200, data={"id": obj.id})

    @swagger_auto_schema(
        operation_summary='添加公共镜像上传任务信息',
        request_body=no_body,
        manual_parameters=[
            openapi.Parameter(
                name='mirrors_image_service_url',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=True,
                description='公共镜像地址',
            ),
            openapi.Parameter(
                name='bucket_name',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=True,
                description='存储桶名称',
            ),
            openapi.Parameter(
                name='file_path',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=True,
                description='文件路径',
            ),
            openapi.Parameter(
                name='token',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=True,
                description='存储桶token',
            ),
            openapi.Parameter(
                name='image_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=True,
                description='镜像id',
            ),

        ],
        responses={
            200: "{'id': 1}"  # 任务id
        }
    )
    @action(methods=['post'], detail=False, url_path=r'image/push', url_name='image-push')
    def mirror_image_task_push(self, request, *args, **kwargs):
        """公共镜像上传"""
        mirrors_image_service_url = request.query_params.get('mirrors_image_service_url', None)
        bucket_name = request.query_params.get('bucket_name', None)
        file_path = request.query_params.get('file_path', None)
        token = request.query_params.get('token', None)
        image_id = request.query_params.get('image_id', None)

        if not mirrors_image_service_url:
            exc = exceptions.Error(msg=f'mirrors_image_service_url 必填')
            return self.exception_response(exc)
        elif not bucket_name:
            exc = exceptions.Error(msg=f'bucket_name 必填')
            return self.exception_response(exc)
        elif not file_path:
            exc = exceptions.Error(msg=f'file_path 必填')
            return self.exception_response(exc)
        elif not token:
            exc = exceptions.Error(msg=f'token 必填')
            return self.exception_response(exc)
        elif not image_id:
            exc = exceptions.Error(msg=f'image_id 必填')
            return self.exception_response(exc)

        task_dict = {'mirrors_image_service_url': mirrors_image_service_url, 'bucket_name': bucket_name,
                     'file_path': file_path, 'token': token}
        task_dict.update({'operate': 2, 'status': 7})

        vo_or_user = request.query_params.get('_who_action', '')
        username = request.user.username
        real_user = ''
        if vo_or_user:
            vo, real_user = extract_string(text=vo_or_user)

        if real_user:
            task_dict.update({'user': real_user})
        else:
            task_dict.update({'user': username})

        hostname = self.get_hostname()
        if hostname:
            task_dict.update({'local_hostname': hostname})

        mirror_image_mamager = MirrorImageManager()

        try:
            obj = mirror_image_mamager.add_mirror_image_push_task(task_dict=task_dict, image_id=image_id)
        except Exception as e:
            return self.exception_response(e)

        return Response(status=200, data={'id': obj.id})

    @swagger_auto_schema(
        operation_summary='启动/暂停/删除任务接口',
        request_body=no_body,
        manual_parameters=[
            openapi.Parameter(
                name='task_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=True,
                description='任务id',
            ),
            openapi.Parameter(
                name='operate',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=True,
                description='操作',
                enum=['start', 'stop', 'delete', 'force_start'],
                default=''
            ),
        ],
        responses={
            200: ''
        }
    )
    @action(methods=['post'], detail=False, url_path=r'image/operate', url_name='operate')
    def mirror_image_task_operate(self, request, *args, **kwargs):
        """"""
        task_id = request.query_params.get('task_id', None)
        operate = request.query_params.get('operate', None)

        if not task_id:
            exc = exceptions.BadRequestError(msg=f'task_id 必填')
            return self.exception_response(exc)
        elif not operate:
            exc = exceptions.BadRequestError(msg=f'operate 必填')
            return self.exception_response(exc)
        elif operate not in ['start', 'stop', 'delete', 'force_start']:
            exc = exceptions.BadRequestError(msg=f'operate 参数信息错误')
            return self.exception_response(exc)

        mirror_image_mamager = MirrorImageManager()

        queryset = mirror_image_mamager.get_mirror_image_task()
        queryset = queryset.filter(id=task_id).first()
        if queryset is None:
            exc = exceptions.BadRequestError(msg=f'task_id 信息错误')
            return self.exception_response(exc)

        if operate == 'start':
            if queryset.status == MirrorImageTask.UPLOADFAILURE or queryset.status == MirrorImageTask.UPLOADCOMPLATE:  # 上传失败或上传完成都可以再次启动任务
                self.execute_task(operate_type='push', task_id=task_id)
            elif queryset.status == MirrorImageTask.DOWNLOADFAILURE or queryset.status == MirrorImageTask.DOWNLOADCOMPLATE:
                self.execute_task(operate_type='pull', task_id=task_id)
            elif queryset.status == MirrorImageTask.NONESTATUS and queryset.operate == MirrorImageTask.OPERATE_PULL:
                self.execute_task(operate_type='pull', task_id=task_id)
            elif queryset.status == MirrorImageTask.NONESTATUS and queryset.operate == MirrorImageTask.OPERATE_PUSH:
                self.execute_task(operate_type='push', task_id=task_id)

        elif operate == 'stop':
            if queryset.status == MirrorImageTask.DOWNLOADING:
                queryset.status = MirrorImageTask.NONESTATUS
                queryset.save(update_fields=['status'])
            if queryset.status == MirrorImageTask.UPLOADING:
                queryset.status = MirrorImageTask.NONESTATUS
                queryset.save(update_fields=['status'])

        elif operate == 'delete':
            try:
                queryset.delete()
            except Exception as e:
                exc = exceptions.BadRequestError(msg=f'删除任务(id={task_id})错误：{str(e)}')
                return self.exception_response(exc)
        elif operate == 'force_start':
            if queryset.operate == MirrorImageTask.OPERATE_PUSH:
                self.execute_task(operate_type='push', task_id=task_id)
            elif queryset.status == MirrorImageTask.OPERATE_PULL:
                self.execute_task(operate_type='pull', task_id=task_id)

        return Response(status=200)

    @swagger_auto_schema(
        operation_summary='修改公共镜像任务信息',
        request_body=no_body,
        manual_parameters=[
            openapi.Parameter(
                name='task_id',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                required=True,
                description='任务id',
            ),
            openapi.Parameter(
                name='token',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description='存储桶token',
            ),
            openapi.Parameter(
                name='bucket_name',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description='存储桶名称',
            ),
            openapi.Parameter(
                name='file_path',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description='文件路径',
            ),
            openapi.Parameter(
                name='service_url',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description='公共镜像地址',
            ),
        ],
        responses={
            200: ''
        }
    )
    @action(methods=['post'], detail=False, url_path=r'image/update', url_name='image-update')
    def mirror_image_task_update(self, request, *args, **kwargs):
        """"""

        task_id = request.query_params.get('task_id', None)
        token = request.query_params.get('token', None)
        bucket_name = request.query_params.get('bucket_name', None)
        mirrors_image_service_url = request.query_params.get('service_url', None)
        file_path = request.query_params.get('file_path', None)

        if not task_id:
            exc = exceptions.BadRequestError(msg=f'task_id 必填')
            return self.exception_response(exc)

        task_info_dict = {}
        if token:
            task_info_dict['token'] = token
        if bucket_name:
            task_info_dict['bucket_name'] = bucket_name
        if mirrors_image_service_url:
            task_info_dict['mirrors_image_service_url'] = mirrors_image_service_url
        if file_path:
            task_info_dict['file_path'] = file_path

        if not task_info_dict:
            return Response(status=200, data={})

        mirror_image_mamager = MirrorImageManager()
        try:
            obj = mirror_image_mamager.modify_mirror_image_pull_task(task_dict=task_info_dict, task_id=task_id)
        except Exception as e:
            exc = exceptions.Error(msg=str(e))
            return self.exception_response(exc)

        return Response(status=200)

    def get_hostname(self):
        hostname = os.uname().nodename
        # ip = socket.gethostbyname(hostname)
        return hostname

    def execute_task(self, operate_type, task_id):
        """执行任务脚本"""
        subprocess.Popen(
            f'python3 /home/uwsgi/evcloud/image/script/mirror_image_task.py -t {task_id} -o {operate_type}', shell=True)
        return

    def get_serializer_class(self):
        if self.action in ['list']:
            return serializers.MirrorImageSerializer

        if self.action == 'mirror_image_task_pull':
            return serializers.MirrorImageCreateSerializer

        return Serializer
