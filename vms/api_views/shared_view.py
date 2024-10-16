from django.utils.translation import gettext as _
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.decorators import action
from rest_framework.serializers import Serializer
from drf_yasg.utils import swagger_auto_schema

from utils.permissions import APIIPPermission
from utils import errors
from api.viewsets import CustomGenericViewSet, serializer_error_msg
from users.managers import UserManager
from vms import serializers as vm_serializers
from vms.models import VmSharedUser
from vms.manager import VmSharedUserManager
from vms.api import VmAPI


class VmSharedUserViewSet(CustomGenericViewSet):
    permission_classes = [IsAuthenticated, APIIPPermission]
    pagination_class = LimitOffsetPagination
    lookup_field = 'vm_id'
    lookup_value_regex = '[0-9a-z-]+'

    @swagger_auto_schema(
        operation_summary='虚拟机的共享用户管理'
    )
    @action(methods=['post'], detail=True, url_path='user/replace', url_name='user-replace')
    def replace_shared_users(self, request, *args, **kwargs):
        """
        虚拟机的共享用户完全替换

            * 把vm的整个共享用户列表替换为提交的新用户列表（可以为空，相当于移除所有共享用户）

            http code 200 ok: no content
        """
        vm_id = kwargs[self.lookup_field]
        try:
            user_roles_dict = self.post_users_validate(request=request)
            vm = VmAPI()._get_user_perms_vm(
                vm_uuid=vm_id, user=request.user,
                allow_superuser=True, allow_resource=True, allow_owner=False
            )
        except errors.Error as exc:
            return self.exception_response(exc)

        users = self.ensure_users_exists(usernames=list(user_roles_dict.keys()))
        users_dict = {u.username: u for u in users}
        VmSharedUserManager.replace_shared_users(vm_id=vm.uuid, user_roles_dict=user_roles_dict, users_dict=users_dict)
        return Response(data=None, status=200)

    def post_users_validate(self, request) -> dict:
        """
        :return:{
            'username1': {'username': 'username1', 'role': 'readonly/readwrite'}
        }
        """
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid(raise_exception=False):
            s_errors = serializer.errors
            if 'users' in s_errors:
                errs = s_errors['users']
                msg = ''
                if isinstance(errs, list):
                    msg = str(errs[0])
                elif isinstance(errs, dict):
                    for idx, err in errs.items():
                        err_msgs = []
                        for k, v in err.items():
                            if v and isinstance(v, list):
                                err_msgs.append(f'{k}: {v[0]}')
                            else:
                                err_msgs.append(f'{k}: {v}')

                        msg = f'index {idx}, ' + ', '.join(err_msgs)
                        break
                else:
                    msg = str(errs)

                raise errors.InvalidParamError(msg=_('提交的用户列表无效。') + msg)
            else:
                msg = serializer_error_msg(s_errors)
                raise errors.BadRequestError(msg=msg)

        user_items = serializer.validated_data['users']
        user_roles_dict = {}
        for u in user_items:
            name = u['username']
            role = u['role']
            if role not in VmSharedUser.Permission.values:
                raise errors.InvalidParamError(msg=_('提交的用户权限无效。'))

            user_roles_dict[name] = u

        return user_roles_dict

    @staticmethod
    def ensure_users_exists(usernames: list):
        return UserManager.get_or_create_users(usernames=usernames)

    def get_serializer_class(self):
        if self.action == 'replace_shared_users':
            return vm_serializers.VmShareUserPostSerializer

        return Serializer
