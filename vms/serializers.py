from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from vms.models import VmSharedUser


class VmSharedUserItem(serializers.Serializer):
    username = serializers.CharField(label=_('用户名'), required=True, min_length=4, max_length=150)
    role = serializers.CharField(label=_('权限'), required=True, help_text=f'{VmSharedUser.Permission.choices}')


class VmShareUserPostSerializer(serializers.Serializer):
    """
    虚拟机共享用户管理序列化器
    """
    users = serializers.ListField(
        label='用户和权限', child=VmSharedUserItem(), required=True, max_length=1024, allow_empty=True)
