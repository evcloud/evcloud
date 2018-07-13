#coding=utf-8

######################################
#@author: bobfu
#@email:  fubo@cnic.cn
#@date:   2015-10-16
#@desc:  api v1.0 视图函数。
#        接受api请求，调用相关api函数进行处理，并转换返回格式。
#        此处不做任何逻辑处理，仅从请求包中获取参数，传入api函数，并将返回值格式化并返回。
######################################
import os
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework import status
from rest_framework.authentication import BasicAuthentication
from rest_framework.compat import coreapi, coreschema
from django.utils.six.moves.urllib import parse as urlparse
from rest_framework.decorators import api_view, authentication_classes, permission_classes, schema
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework.schemas.inspectors import AutoSchema

from .center import get_list as api_center_get_list
from .ceph import get_list as api_ceph_get_list
from .error import ERROR_CN, ERR_AUTH_PERM,ERR_ARGS_REQUIRED
from .group import get_list as api_group_get_list, get as api_group_get
from .host import get_list as api_host_get_list, get as api_host_get
from .images import get as api_image_get, get_list as api_image_get_list
from .net import get_vlan as api_net_get_vlan, get_vlan_list as api_net_get_vlan_list
from .vm import create as  api_vm_create
from .vm import edit as api_vm_edit
from .vm import get as api_vm_get
from .vm import get_list as api_vm_get_list
from .vm import op as api_vm_op
from .vm import status as api_vm_status
from .vnc import open as api_vnc_open, close as api_vnc_close
from .volume import get_list as api_volume_get_list
from .volume import get as api_volume_get
from .volume import create as api_volume_create
from .volume import delete as api_volume_delete
from .volume import mount as api_volume_mount
from .volume import umount as api_volume_umount
from .volume import set_remark as api_volume_set_remark


class MethodSchema(AutoSchema):
    """
        BobFu 2017-12-12
        Change manual_fields to support define fields in different method
    """
    def get_link(self, path, method, base_url):
        fields = self.get_path_fields(path, method)
        fields += self.get_serializer_fields(path, method)
        fields += self.get_pagination_fields(path, method)
        fields += self.get_filter_fields(path, method)

        if type(self._manual_fields) is dict and method in self._manual_fields:
            by_name = {f.name: f for f in fields}
            for f in self._manual_fields[method]:
                by_name[f.name] = f
            fields = list(by_name.values())

        if fields and any([field.location in ('form', 'body') for field in fields]):
            encoding = self.get_encoding(path, method)
        else:
            encoding = None

        description = self.get_description(path, method)

        if base_url and path.startswith('/'):
            path = path[1:]
        
        return coreapi.Link(
            url=os.path.join(base_url or '', path),
            action=method.lower(),
            encoding=encoding,
            fields=fields,
            description=description
        )


class HasApiPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.api_user


@api_view(['GET'])
@authentication_classes((OAuth2Authentication, BasicAuthentication))
@permission_classes((IsAuthenticated, HasApiPermission))
def center_list(request, format=None):
    if request.method == 'GET':
        args = {
            'req_user': request.user,
        }
        dic = api_center_get_list(args)
        if dic['res']:
            return Response(dic['list'], status=status.HTTP_200_OK)
        return Response({'detail': ERROR_CN.get(dic['err'], dic['err'])}, status=status.HTTP_404_NOT_FOUND)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
@authentication_classes((OAuth2Authentication, BasicAuthentication))
@permission_classes((IsAuthenticated, HasApiPermission))
@schema(MethodSchema(manual_fields={
    'GET': [
        coreapi.Field(name='center_id', location='query', required=False, schema=coreschema.Integer())
    ]
}))
def group_list(request, format=None):
    if request.method == 'GET':
        args = {
            'req_user': request.user,
            'center_id': request.GET.get('center_id'),
        }
        dic = api_group_get_list(args)
        if dic['res']:
            return Response(dic['list'], status=status.HTTP_200_OK)
        return Response(status=status.HTTP_404_NOT_FOUND)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
@authentication_classes((OAuth2Authentication, BasicAuthentication))
@permission_classes((IsAuthenticated, HasApiPermission))
def group_detail(request, group_id, format=None):
    if request.method == 'GET':
        param = {
            'req_user': request.user,
            'group_id': group_id
        }
        dic = api_group_get(param)
        if dic['res']:
            return Response(dic['info'], status=status.HTTP_200_OK)
        if dic['err'] == ERR_AUTH_PERM:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response({'detail': ERROR_CN.get(dic['err'], dic['err'])}, status=status.HTTP_404_NOT_FOUND)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
@authentication_classes((OAuth2Authentication, BasicAuthentication))
@permission_classes((IsAuthenticated, HasApiPermission))
@schema(MethodSchema(manual_fields={
    'GET': [
        coreapi.Field(name='center_id', location='query', required=True, schema=coreschema.Integer()),
        coreapi.Field(name='group_id', location='query', required=False, schema=coreschema.Integer())
    ]
}))
def pool_list(request, format=None):
    if request.method == 'GET':
        args = {
            'req_user': request.user,
            'center_id': request.GET.get('center_id'),
            'group_id': request.GET.get('group_id'),
        }
        dic = api_ceph_get_list(args)
        if dic['res']:
            return Response(dic['list'], status=status.HTTP_200_OK)
        if dic['err'] == ERR_AUTH_PERM:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response({'detail': ERROR_CN.get(dic['err'], dic['err'])}, status=status.HTTP_404_NOT_FOUND)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
@authentication_classes((OAuth2Authentication, BasicAuthentication))
@permission_classes((IsAuthenticated, HasApiPermission))
@schema(MethodSchema(manual_fields={
    'GET': [
        coreapi.Field(name='group_id', location='query', required=True, schema=coreschema.Integer())
    ]
}))
def host_list(request, format=None):
    if request.method == 'GET':
        args = {
            'req_user': request.user,
            'group_id': request.GET.get('group_id'),
        }
        dic = api_host_get_list(args)
        if dic['res']:
            return Response(dic['list'], status=status.HTTP_200_OK)
        if dic['err'] == ERR_AUTH_PERM:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response({'detail': ERROR_CN.get(dic['err'], dic['err'])}, status=status.HTTP_404_NOT_FOUND)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
@authentication_classes((OAuth2Authentication, BasicAuthentication))
@permission_classes((IsAuthenticated, HasApiPermission))
def host_detail(request, host_id, format=None):
    if request.method == 'GET':
        param = {
            'req_user': request.user,
            'host_id': host_id
        }
        dic = api_host_get(param)
        if dic['res']:
            return Response(dic['info'], status=status.HTTP_200_OK)
        if dic['err'] == ERR_AUTH_PERM:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response({'detail': ERROR_CN.get(dic['err'], dic['err'])}, status=status.HTTP_404_NOT_FOUND)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
@authentication_classes((OAuth2Authentication, BasicAuthentication))
@permission_classes((IsAuthenticated, HasApiPermission))
@schema(MethodSchema(manual_fields={
    'GET': [
        coreapi.Field(name='pool_id', location='query', required=True, schema=coreschema.Integer())
    ]
}))
def image_list(request):
    if request.method == 'GET':
        args = {
            'req_user': request.user,
            'ceph_id': request.GET.get('pool_id')
        }
        dic = api_image_get_list(args)
        if dic['res']:
            return Response(dic['list'], status=status.HTTP_200_OK)
        if dic['err'] == ERR_AUTH_PERM:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response({'detail': ERROR_CN.get(dic['err'], dic['err'])}, status=status.HTTP_404_NOT_FOUND)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
@authentication_classes((OAuth2Authentication, BasicAuthentication))
@permission_classes((IsAuthenticated, HasApiPermission))
def image_detail(request, image_id, format=None):
    if request.method == 'GET':
        args = {
            'req_user': request.user,
            'image_id': image_id
        }
        dic = api_image_get(args)
        if dic['res']:
            return Response(dic['info'], status=status.HTTP_200_OK)
        if dic['err'] == ERR_AUTH_PERM:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response({'detail': ERROR_CN.get(dic['err'], dic['err'])}, status=status.HTTP_404_NOT_FOUND)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET', 'POST'])
@authentication_classes((OAuth2Authentication, BasicAuthentication))
@permission_classes((IsAuthenticated, HasApiPermission))
@schema(MethodSchema(manual_fields={
    'GET': [
        coreapi.Field(name='group_id', location='query', required=True, schema=coreschema.Integer())
    ],
    'POST': [
        coreapi.Field(name='image_id', location='form', required=True, schema=coreschema.Integer()),
        coreapi.Field(name='vcpu', location='form', required=True, schema=coreschema.Integer()),
        coreapi.Field(name='mem', location='form', required=True, schema=coreschema.Integer()),
        coreapi.Field(name='group_id', location='form', required=True, schema=coreschema.Integer()),
        coreapi.Field(name='host_id', location='form', required=False, schema=coreschema.Integer()),
        coreapi.Field(name='net_type_id', location='form', required=False, schema=coreschema.Integer(),
                      description='net_type_id or vlan_id required.'),
        coreapi.Field(name='vlan_id', location='form', required=False, schema=coreschema.Integer(),
                      description='net_type_id or vlan_id required.'),
        coreapi.Field(name='diskname', location='form', required=False, schema=coreschema.String()),
        coreapi.Field(name='remarks', location='form', required=False, schema=coreschema.String()),
    ],
}))
def vm_list(request):
    if request.method == 'GET':
        args = {
            'req_user': request.user,
            'group_id': request.GET.get('group_id'),
        }
        dic = api_vm_get_list(args)
        if dic['res']:
            return Response(dic['list'], status=status.HTTP_200_OK)
        if dic['err'] == ERR_AUTH_PERM:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response({'detail': ERROR_CN.get(dic['err'], dic['err'])}, status=status.HTTP_404_NOT_FOUND)

    elif request.method == 'POST':
        args = {
            'req_user': request.user,
            'creator': request.user.username,
        }
        for k in ['image_id', 'vcpu', 'mem', 'group_id', 'host_id', 'net_type_id', 'vlan_id', 'diskname', 'remarks']:
            args[k] = request.data.get(k)

        dic = api_vm_create(args)

        if dic['res']:
            return Response(dic['uuid'], status=status.HTTP_201_CREATED)
        if dic['err'] == ERR_AUTH_PERM:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response({'detail': ERROR_CN.get(dic['err'], dic['err'])}, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET', 'PATCH', 'DELETE'])
@authentication_classes((OAuth2Authentication, BasicAuthentication))
@permission_classes((IsAuthenticated, HasApiPermission))
@schema(MethodSchema(manual_fields={
    'PATCH': [
        coreapi.Field(name='vcpu', location='form', required=False, schema=coreschema.Integer()),
        coreapi.Field(name='mem', location='form', required=False, schema=coreschema.Integer()),
        coreapi.Field(name='remarks', location='form', required=False, schema=coreschema.String()),
    ],
}))
def vm_detail(request, vm_id, format=None):
    if request.method == 'GET':
        args = {
            'req_user': request.user,
            'uuid': vm_id
        }
        dic = api_vm_get(args)
        if dic['res']:
            return Response(dic['info'], status=status.HTTP_200_OK)
        if dic['err'] == ERR_AUTH_PERM:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response({'detail': ERROR_CN.get(dic['err'], dic['err'])}, status=status.HTTP_404_NOT_FOUND)

    elif request.method == "PATCH":
        args = {
            'req_user': request.user,
            'uuid': vm_id,
        }
        for k in ['vcpu', 'mem', 'remarks']:
            args[k] = request.data.get(k)

        dic = api_vm_edit(args)

        if dic['res']:
            return Response(status=status.HTTP_201_CREATED)
        if dic['err'] == ERR_AUTH_PERM:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response({'detail': ERROR_CN.get(dic['err'], dic['err'])}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        args = {
            'req_user': request.user,
            'uuid': vm_id,
            'op': 'delete',
        }
        dic = api_vm_op(args)
        if dic['res']:
            return Response(status=status.HTTP_204_NO_CONTENT)
        if dic['err'] == ERR_AUTH_PERM:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response({'detail': ERROR_CN.get(dic['err'], dic['err'])}, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
@authentication_classes((OAuth2Authentication, BasicAuthentication))
@permission_classes((IsAuthenticated, HasApiPermission))
def vm_status(request, vm_id, format=None):
    if request.method == 'GET':
        args = {
            'req_user': request.user,
            'uuid': vm_id
        }
        dic = api_vm_status(args)
        if dic['res']:
            return Response(dic['status'], status=status.HTTP_200_OK)
        if dic['err'] == ERR_AUTH_PERM:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response({'detail': ERROR_CN.get(dic['err'], dic['err'])}, status=status.HTTP_404_NOT_FOUND)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['PATCH'])
@authentication_classes((OAuth2Authentication, BasicAuthentication))
@permission_classes((IsAuthenticated, HasApiPermission))
@schema(MethodSchema(manual_fields={
    'PATCH': [
        coreapi.Field(name='op', location='form', required=True, schema=coreschema.Enum(
            enum=['start', 'reboot', 'shutdown', 'poweroff'])),
    ],
}))
def vm_operations(request, vm_id, format=None):
    if request.method == 'PATCH':
        args = {
            'req_user': request.user,
            'uuid': vm_id,
            'op': request.data.get('op'),
        }
        print(args)

        dic = api_vm_op(args)
        if dic['res']:
            return Response(status=status.HTTP_201_CREATED)
        if dic['err'] == ERR_AUTH_PERM:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response({'detail': ERROR_CN.get(dic['err'], dic['err'])}, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
@authentication_classes((OAuth2Authentication, BasicAuthentication))
@permission_classes((IsAuthenticated, HasApiPermission))
def vm_vnc(request, vm_id, format=None):
    if request.method == 'POST':
        # Create VNC
        try:
            dic = api_vnc_open({
                'req_user': request.user,
                'uuid': vm_id,
            })
            print(dic)
            if dic['res']:
                http_host = request.META['HTTP_HOST']
                return Response({
                    'url': 'http://' + http_host + dic['url'],
                    'vncid': dic['vncid'],
                }, status=status.HTTP_201_CREATED)
            if dic['err'] == ERR_AUTH_PERM:
                return Response(status=status.HTTP_403_FORBIDDEN)
            return Response({'detail': ERROR_CN.get(dic['err'], dic['err'])}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as e:
            return Response({'detail': '操作失败'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['DELETE'])
@authentication_classes((OAuth2Authentication, BasicAuthentication))
@permission_classes((IsAuthenticated, HasApiPermission))
def vnc_detail(request, vnc_id, format=None):
    if request.method == 'DELETE':
        # Delete VNC
        try:
            dic = api_vnc_close({
                'req_user': request.user,
                "vncid": vnc_id,
            })
            if dic['res']:
                return Response(status=status.HTTP_204_NO_CONTENT)
            if dic['err'] == ERR_AUTH_PERM:
                return Response(status=status.HTTP_403_FORBIDDEN)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({'detail': '操作失败'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
@authentication_classes((OAuth2Authentication, BasicAuthentication))
@permission_classes((IsAuthenticated, HasApiPermission))
@schema(MethodSchema(manual_fields={
    'GET': [
        coreapi.Field(name='group_id', location='query', required=True, schema=coreschema.Integer())
    ]
}))
def vlan_list(request, format=None):
    if request.method == 'GET':
        args = {
            'req_user': request.user,
            'group_id': request.GET.get('group_id'),
        }
        dic = api_net_get_vlan_list(args)
        if dic['res']:
            return Response(dic['list'], status=status.HTTP_200_OK)
        if dic['err'] == ERR_AUTH_PERM:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response({'detail': ERROR_CN.get(dic['err'], dic['err'])}, status=status.HTTP_404_NOT_FOUND)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
@authentication_classes((OAuth2Authentication, BasicAuthentication))
@permission_classes((IsAuthenticated, HasApiPermission))
def vlan_detail(request, vlan_id, format=None):
    if request.method == 'GET':
        args = {
            'req_user': request.user,
            'vlan_id': vlan_id
        }
        dic = api_net_get_vlan(args)

        if dic['res']:
            return Response(dic['info'], status=status.HTTP_200_OK)
        if dic['err'] == ERR_AUTH_PERM:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(status=status.HTTP_404_NOT_FOUND)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)



@api_view(['GET', 'POST'])
@authentication_classes((OAuth2Authentication, BasicAuthentication))
@permission_classes((IsAuthenticated, HasApiPermission))
@schema(MethodSchema(manual_fields={
    'GET': [
        coreapi.Field(name='group_id', location='query', required=True, schema=coreschema.Integer())
    ],
    'POST': [
        coreapi.Field(name='group_id', location='form', required=True, schema=coreschema.Integer()),
        coreapi.Field(name='cephpool_id', location='form', required=True, schema=coreschema.Integer()),
        coreapi.Field(name='size', location='form', required=True, schema=coreschema.Integer()),        
        coreapi.Field(name='remarks', location='form', required=False, schema=coreschema.String()),
    ],
}))
def volume_list(request):    
    if request.method == 'GET':
        args = {
            'req_user': request.user,
            'group_id': request.GET.get('group_id'),
        }
        dic = api_volume_get_list(args)
        if dic['res']:
            return Response(dic['list'], status=status.HTTP_200_OK)
        if dic['err'] == ERR_AUTH_PERM:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response({'detail': ERROR_CN.get(dic['err'], dic['err'])}, status=status.HTTP_404_NOT_FOUND)

    elif request.method == 'POST':
        args = {
            'req_user': request.user,
            'group_id':request.data.get('group_id'),
            'pool_id':request.data.get('cephpool_id'),
            'size':request.data.get('size') * 1024
        }
        dic = api_volume_create(args)
        remarks = request.data.get('remarks')
        if dic['res']:
            api_volume_set_remark({
                       'req_user': args['req_user'],
                       'volume_id': dic['volume_id'], 
                       'remarks': remarks})        

        if dic['res']:
            return Response(dic['volume_id'], status=status.HTTP_201_CREATED)
        if dic['err'] == ERR_AUTH_PERM:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response({'detail': ERROR_CN.get(dic['err'], dic['err'])}, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET', 'PATCH', 'DELETE'])
@authentication_classes((OAuth2Authentication, BasicAuthentication))
@permission_classes((IsAuthenticated, HasApiPermission))
@schema(MethodSchema(manual_fields={
    'PATCH': [
        coreapi.Field(name='remarks', location='form', required=False, schema=coreschema.String()),
    ],
}))
def volume_detail(request, volume_id, format=None):
    if request.method == 'GET':
        args = {
            'req_user': request.user,
            'volume_id': volume_id
        }

        dic = api_volume_get(args)

        if dic['res']:
            return Response(dic['info'], status=status.HTTP_200_OK)
        if dic['err'] == ERR_AUTH_PERM:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response({'detail': ERROR_CN.get(dic['err'], dic['err'])}, status=status.HTTP_404_NOT_FOUND)

    elif request.method == "PATCH":
        args = {
            'req_user': request.user,
            'volume_id': volume_id,
        }
        args['remarks'] = request.data.get('remarks')

        dic = api_volume_set_remark(args)
        print(dic)

        if dic['res']:
            return Response(status=status.HTTP_201_CREATED)
        if dic['err'] == ERR_AUTH_PERM:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response({'detail': ERROR_CN.get(dic['err'], dic['err'])}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        args = {
            'req_user': request.user,
            'volume_id': volume_id,
        }
        dic = api_volume_delete(args)
        if dic['res']:
            return Response(status=status.HTTP_204_NO_CONTENT)
        if dic['err'] == ERR_AUTH_PERM:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response({'detail': ERROR_CN.get(dic['err'], dic['err'])}, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)



@api_view(['PATCH'])
@authentication_classes((OAuth2Authentication, BasicAuthentication))
@permission_classes((IsAuthenticated, HasApiPermission))
@schema(MethodSchema(manual_fields={
    'PATCH': [
        coreapi.Field(name='op', location='form', required=True, schema=coreschema.Enum(
            enum=['mount', 'unmount'])),
        coreapi.Field(name='vm_id', location='form', required=False, schema=coreschema.String()),        
    ],
}))
def volume_vm(request, volume_id, format=None):
    if request.method == 'PATCH':
        args = {
            'req_user': request.user,
            'vm_uuid': request.data.get('vm_id'),
            'volume_id':volume_id
        }
        op = request.data.get('op')

        if op == 'mount' and args['vm_uuid']:
            dic = api_volume_mount(args)
        elif op == 'unmount':
            dic = api_volume_umount(args)
        else :
            dic = {'res':False,'err':ERR_ARGS_REQUIRED}
    
        if dic['res']:
            return Response(status=status.HTTP_201_CREATED)
        if dic['err'] == ERR_AUTH_PERM:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response({'detail': ERROR_CN.get(dic['err'], dic['err'])}, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
