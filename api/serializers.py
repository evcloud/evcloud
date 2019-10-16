from rest_framework import serializers

from vms.models import Vm



class VmSerializer(serializers.ModelSerializer):
    '''
    虚拟机序列化器
    '''
    user = serializers.SerializerMethodField() # 自定义user字段内容
    create_time = serializers.SerializerMethodField()  # 自定义字段内容
    host = serializers.SerializerMethodField()
    mac_ip = serializers.SerializerMethodField()
    uuid = serializers.SerializerMethodField()

    class Meta:
        model = Vm
        fields = ('uuid', 'name', 'vcpu', 'mem', 'disk', 'host', 'mac_ip', 'user', 'create_time')
        # depth = 1

    def get_uuid(self, obj):
        return obj.get_uuid()

    def get_user(selfself, obj):
        return {'id': obj.user.id, 'username': obj.user.username}

    def get_create_time(self, obj):
        if not obj.create_time:
            return ''
        return obj.create_time.strftime('%Y-%m-%d %H:%M:%S')

    def get_host(self, obj):
        return obj.host.ipv4

    def get_mac_ip(self, obj):
        return obj.mac_ip.ipv4


class VmCreateSerializer(serializers.Serializer):
    '''
    创建虚拟机序列化器
    '''
    image_id = serializers.IntegerField(label='镜像id', required=True, min_value=1, help_text='系统镜像id')
    vcpu = serializers.IntegerField(label='cpu数', required=True, min_value=1, help_text='cpu数')
    mem = serializers.IntegerField(label='内存大小', required=True, min_value=200)
    vlan_id = serializers.IntegerField(label='子网id', required=True, min_value=1, help_text='子网id')
    group_id = serializers.IntegerField(label='宿主机组id', required=False, min_value=1, help_text='宿主机组id', default=None)
    host_id = serializers.IntegerField(label='宿主机id', required=False, min_value=1, help_text='宿主机id', default=None)
    remarks = serializers.CharField(label='备注', required=False, max_length=255, default='')

    def validate(self, data):
        group_id = data.get('group_id')
        host_id = data.get('host_id')

        if not group_id and not host_id:
            raise serializers.ValidationError(detail={'code_text': 'group_id和host_id参数必须提交其中一个'})
        return data


class VmPatchSerializer(serializers.Serializer):
    '''
    创建虚拟机序列化器
    '''
    vcpu = serializers.IntegerField(label='cpu数', required=False, min_value=1, help_text='cpu数')
    mem = serializers.IntegerField(label='内存大小', required=False, min_value=200)

    def validate(self, data):
        return data



