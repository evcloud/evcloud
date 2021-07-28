from rest_framework import serializers

from vms.models import Vm, MigrateTask
from compute.models import Center, Group, Host
from network.models import Vlan
from image.models import Image
from vdisk.models import Vdisk


class VmSerializer(serializers.ModelSerializer):
    """
    虚拟机序列化器
    """
    user = serializers.SerializerMethodField()  # 自定义user字段内容
    create_time = serializers.DateTimeField()  # format='%Y-%m-%d %H:%M:%S'
    host = serializers.SerializerMethodField()
    mac_ip = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    ip = serializers.SerializerMethodField()

    class Meta:
        model = Vm
        fields = ('uuid', 'name', 'vcpu', 'mem', 'image', 'disk', 'host', 'mac_ip', 'ip', 'user', 'create_time')
        # depth = 1

    @staticmethod
    def get_user(obj):
        return {'id': obj.user.id, 'username': obj.user.username}

    @staticmethod
    def get_host(obj):
        return obj.host.ipv4

    @staticmethod
    def get_mac_ip(obj):
        return obj.mac_ip.ipv4

    @staticmethod
    def get_ip(obj):
        if obj.mac_ip.vlan:
            public = obj.mac_ip.vlan.tag == obj.mac_ip.vlan.NET_TAG_PUBLIC
        else:
            public = False
        return {'ipv4': obj.mac_ip.ipv4, 'public_ipv4': public}

    @staticmethod
    def get_image(obj):
        img = obj.image
        return img.name if img else ""


class VmCreateSerializer(serializers.Serializer):
    """
    创建虚拟机序列化器
    """
    image_id = serializers.IntegerField(label='镜像id', required=True, min_value=1, help_text='系统镜像id')
    vcpu = serializers.IntegerField(label='cpu数', min_value=1, required=False,
                                    allow_null=True, default=None, help_text='cpu数')
    mem = serializers.IntegerField(label='内存大小', min_value=512, required=False,
                                   allow_null=True, default=None, help_text='单位MB')
    vlan_id = serializers.IntegerField(label='子网id', required=False, allow_null=True,
                                       min_value=1, help_text='子网id', default=None)
    center_id = serializers.IntegerField(label='分中心id', required=False, allow_null=True,
                                         min_value=1, help_text='分中心id', default=None)
    group_id = serializers.IntegerField(label='宿主机组id', required=False, allow_null=True,
                                        min_value=1, help_text='宿主机组id', default=None)
    host_id = serializers.IntegerField(label='宿主机id', required=False, allow_null=True,
                                       min_value=1, help_text='宿主机id', default=None)
    remarks = serializers.CharField(label='备注', required=False, allow_blank=True, max_length=255, default='')
    ipv4 = serializers.CharField(label='ipv4', required=False, allow_blank=True, max_length=255, default='')
    flavor_id = serializers.IntegerField(label='配置样式id', required=False, allow_null=True,
                                         default=None, help_text='配置样式id')

    def validate(self, data):
        center_id = data.get('center_id')
        group_id = data.get('group_id')
        host_id = data.get('host_id')

        vcpu = data.get('vcpu')
        mem = data.get('mem')
        flavor_id = data.get('flavor_id')

        if not group_id and not host_id and not center_id:
            raise serializers.ValidationError(detail={'code_text': 'center_id、group_id和host_id参数必须提交其中一个'})

        if (not flavor_id) and (not (vcpu and mem)):
            raise serializers.ValidationError(detail={'code_text': '必须提交flavor_id或者直接指定vcpu和mem)'})
        return data


class VmPatchSerializer(serializers.Serializer):
    """
    创建虚拟机序列化器
    """
    flavor_id = serializers.IntegerField(label='配置样式id', required=False, allow_null=True, default=None,
                                         help_text='配置样式id')
    vcpu = serializers.IntegerField(label='cpu数', min_value=1, required=False, allow_null=True, default=0,
                                    help_text='cpu数')
    mem = serializers.IntegerField(label='内存大小', min_value=512, required=False, allow_null=True, default=0,
                                   help_text='单位MB')

    def validate(self, data):
        vcpu = data.get('vcpu')
        mem = data.get('mem')
        flavor_id = data.get('flavor_id')

        if (not flavor_id) and (not vcpu and not mem):
            raise serializers.ValidationError(detail={'code_text': '必须提交flavor_id或者直接指定vcp或mem)'})
        return data


class CenterSerializer(serializers.ModelSerializer):
    """
    分中心序列化器
    """
    class Meta:
        model = Center
        fields = ('id', 'name', 'location', 'desc')


class GroupSerializer(serializers.ModelSerializer):
    """
    宿主机组序列化器
    """
    class Meta:
        model = Group
        fields = ('id', 'name', 'center', 'desc')


class HostSerializer(serializers.ModelSerializer):
    """
    宿主机序列化器
    """
    class Meta:
        model = Host
        fields = ('id', 'ipv4', 'group', 'vcpu_total', 'vcpu_allocated', 'mem_total', 'mem_allocated',
                  'mem_reserved', 'vm_limit', 'vm_created', 'enable', 'desc')


class VlanSerializer(serializers.ModelSerializer):
    """
    子网网段序列化器
    """
    class Meta:
        model = Vlan
        fields = ('id', 'name', 'br', 'tag', 'enable', 'subnet_ip', 'net_mask', 'gateway', 'dns_server', 'remarks')


class ImageSerializer(serializers.ModelSerializer):
    """
    子网网段序列化器
    """
    tag = serializers.SerializerMethodField()
    sys_type = serializers.SerializerMethodField()
    create_time = serializers.DateTimeField()

    class Meta:
        model = Image
        fields = ('id', 'name', 'version', 'sys_type', 'tag', 'enable', 'create_time', 'desc',
                  'default_user', 'default_password')

    @staticmethod
    def get_tag(obj):
        return {'id': obj.tag, 'name': obj.tag_display}

    @staticmethod
    def get_sys_type(obj):
        return {'id': obj.sys_type, 'name': obj.sys_type_display}


class AuthTokenDumpSerializer(serializers.Serializer):
    key = serializers.CharField()
    user = serializers.SerializerMethodField()
    created = serializers.DateTimeField()

    @staticmethod
    def get_user(obj):
        return obj.user.username


class UserSimpleSerializer(serializers.Serializer):
    """用户极简序列化器"""
    id = serializers.IntegerField()
    username = serializers.CharField()


class QuotaSimpleSerializer(serializers.Serializer):
    """硬盘存储池配额极简序列化器"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    pool = serializers.SerializerMethodField(method_name='get_pool')
    ceph = serializers.SerializerMethodField(method_name='get_ceph')
    group = serializers.SerializerMethodField(method_name='get_group')

    @staticmethod
    def get_pool(obj):
        pool = obj.cephpool
        if not pool:
            return {}

        return {'id': pool.id, 'name': pool.pool_name}

    @staticmethod
    def get_ceph(obj):
        pool = obj.cephpool
        if not pool:
            return {}

        ceph = pool.ceph
        if not ceph:
            return {}
        return {'id': ceph.id, 'name': ceph.name}

    @staticmethod
    def get_group(obj):
        group = obj.group
        if not group:
            return {}
        return {'id': group.id, 'name': group.name}


class QuotaListSerializer(QuotaSimpleSerializer):
    """硬盘存储池配额列表序列化器"""
    total = serializers.IntegerField()
    size_used = serializers.IntegerField()
    max_vdisk = serializers.IntegerField()


class VdiskSerializer(serializers.ModelSerializer):
    """
    虚拟硬盘序列化器
    """
    group = serializers.SerializerMethodField()
    quota = serializers.SerializerMethodField()
    vm = serializers.SerializerMethodField()
    user = UserSimpleSerializer(required=False)  # May be an anonymous user
    create_time = serializers.DateTimeField()
    attach_time = serializers.DateTimeField()

    class Meta:
        model = Vdisk
        fields = ('uuid', 'size', 'vm', 'user', 'quota', 'create_time', 'attach_time', 'enable', 'remarks', 'group')
        depth = 0

    @staticmethod
    def get_group(obj):
        group = obj.quota.group
        if not group:
            return group
        return {'id': group.id, 'name': group.name}

    @staticmethod
    def get_quota(obj):
        quota = obj.quota
        if not quota:
            return quota
        return {'id': quota.id, 'name': quota.name}

    @staticmethod
    def get_vm(obj):
        vm = obj.vm
        if vm:
            return {'uuid': vm.hex_uuid, 'ipv4': vm.mac_ip.ipv4}
        return vm


class VdiskDetailSerializer(serializers.ModelSerializer):
    """
    虚拟硬盘详细信息序列化器
    """
    user = UserSimpleSerializer(required=False)  # May be an anonymous user
    quota = QuotaSimpleSerializer(required=False)
    vm = serializers.SerializerMethodField()
    create_time = serializers.DateTimeField()
    attach_time = serializers.DateTimeField()

    class Meta:
        model = Vdisk
        fields = ('uuid', 'size', 'vm', 'user', 'quota', 'create_time', 'attach_time', 'enable', 'remarks')
        depth = 1

    @staticmethod
    def get_vm(obj):
        vm = obj.vm
        if vm:
            return {'uuid': vm.hex_uuid, 'ipv4': vm.mac_ip.ipv4}
        return vm


class VdiskCreateSerializer(serializers.Serializer):
    """
    虚拟硬盘创建序列化器
    """
    size = serializers.IntegerField(label='容量大小（GB）', required=True, min_value=1, help_text='容量大小,单位GB')
    quota_id = serializers.IntegerField(label='硬盘存储池id', required=False, allow_null=True,
                                        min_value=1, help_text='宿主机组id', default=None)
    group_id = serializers.IntegerField(label='宿主机组id', required=False, allow_null=True,
                                        min_value=1, help_text='宿主机组id', default=None)
    center_id = serializers.IntegerField(label='分中心id', required=False, allow_null=True,
                                         min_value=1, help_text='分中心id', default=None)
    remarks = serializers.CharField(label='备注', required=False, allow_blank=True, default='')

    def validate(self, data):
        center_id = data.get('center_id')
        group_id = data.get('group_id')
        quota_id = data.get('quota_id')

        if not group_id and not quota_id and not center_id:
            raise serializers.ValidationError(detail={'code_text': 'center_id、group_id和quota_id参数必须提交其中一个'})
        return data


class VmDiskSnapSerializer(serializers.Serializer):
    """
    虚拟机系统盘快照序列化器
    """
    id = serializers.IntegerField()
    vm = serializers.SerializerMethodField()
    snap = serializers.CharField()
    create_time = serializers.DateTimeField()
    remarks = serializers.CharField()

    @staticmethod
    def get_vm(obj):
        vm = obj.vm
        if vm:
            return {'uuid': vm.hex_uuid, 'ipv4': vm.mac_ip.ipv4}
        return vm


class PCIDeviceSerializer(serializers.Serializer):
    """
    PCI设备序列化器
    """
    id = serializers.IntegerField()
    type = serializers.SerializerMethodField()
    vm = serializers.SerializerMethodField()
    host = serializers.SerializerMethodField()
    attach_time = serializers.DateTimeField()
    remarks = serializers.CharField()

    @staticmethod
    def get_vm(obj):
        vm = obj.vm
        if vm:
            return {'uuid': vm.hex_uuid, 'ipv4': vm.mac_ip.ipv4}
        return vm

    @staticmethod
    def get_host(obj):
        host = obj.host
        if host:
            return {'id': host.id, 'ipv4': host.ipv4}
        return host

    @staticmethod
    def get_type(obj):
        return {'val': obj.type, 'name': obj.type_display}


class MacIPSerializer(serializers.Serializer):
    """
    MAC IP序列化器
    """
    id = serializers.IntegerField()
    mac = serializers.CharField(max_length=17, help_text='MAC地址')
    ipv4 = serializers.IPAddressField(help_text='IP地址')
    used = serializers.BooleanField(help_text='是否已分配给虚拟机使用')


class VmDetailSerializer(serializers.ModelSerializer):
    """
    虚拟机详情序列化器
    """
    user = serializers.SerializerMethodField()  # 自定义user字段内容
    create_time = serializers.DateTimeField()
    host = serializers.SerializerMethodField()
    mac_ip = serializers.SerializerMethodField()
    ip = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    image_info = serializers.SerializerMethodField()
    vdisks = serializers.SerializerMethodField()
    pci_devices = serializers.SerializerMethodField()

    class Meta:
        model = Vm
        fields = ('uuid', 'name', 'vcpu', 'mem', 'image', 'image_info', 'disk', 'host', 'mac_ip', 'ip', 'user', 'create_time',
                  'vdisks', 'pci_devices')
        # depth = 1

    @staticmethod
    def get_user(obj):
        return {'id': obj.user.id, 'username': obj.user.username}

    @staticmethod
    def get_host(obj):
        return obj.host.ipv4

    @staticmethod
    def get_mac_ip(obj):
        return obj.mac_ip.ipv4

    @staticmethod
    def get_ip(obj):
        if obj.mac_ip.vlan:
            public = obj.mac_ip.vlan.tag == obj.mac_ip.vlan.NET_TAG_PUBLIC
        else:
            public = False
        return {'ipv4': obj.mac_ip.ipv4, 'public_ipv4': public}

    @staticmethod
    def get_image(obj):
        img = obj.image
        return img.name if img else ""

    @staticmethod
    def get_image_info(obj):
        img = obj.image
        if img:
            return {
                'id': img.id, 'name': img.name, 'desc': img.desc,
                'default_user': img.default_user, 'default_password': img.default_password
            }

        return None

    @staticmethod
    def get_vdisks(obj):
        vdisks = obj.vdisks.select_related('quota__group', 'vm__mac_ip', 'user')
        return VdiskSerializer(instance=vdisks, many=True, required=False).data

    @staticmethod
    def get_pci_devices(obj):
        devs = obj.pci_devices.select_related('host__group', 'vm')
        return PCIDeviceSerializer(instance=devs, many=True, required=False).data


class VmChangePasswordSerializer(serializers.Serializer):
    """
    虚拟主机修改密码
    """
    username = serializers.CharField(label='用户名', required=True, help_text='虚拟主机系统用户名')
    password = serializers.CharField(min_length=6, max_length=20, label='新密码', required=True, help_text='新密码')


class FlavorSerializer(serializers.Serializer):
    id = serializers.IntegerField(label='配置样式')
    vcpus = serializers.IntegerField(label='虚拟CPU数')
    ram = serializers.IntegerField(label='内存MB')


class VPNCreateSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, min_length=1, max_length=150)
    password = serializers.CharField(required=False, min_length=6, max_length=64, default='', help_text='如果未指定，随机分配密码')


class VPNSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    active = serializers.BooleanField()
    create_time = serializers.DateTimeField()
    modified_time = serializers.DateTimeField()


class MigrateTaskSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    vm_uuid = serializers.CharField()

    src_host_id = serializers.IntegerField()
    src_host_ipv4 = serializers.CharField()
    src_undefined = serializers.BooleanField()
    src_is_free = serializers.BooleanField()

    dst_host_id = serializers.IntegerField()
    dst_host_ipv4 = serializers.CharField()
    dst_is_claim = serializers.BooleanField()

    migrate_time = serializers.DateTimeField()
    migrate_complete_time = serializers.DateTimeField()
    status = serializers.CharField(help_text=f'{MigrateTask.Status.choices}')
    content = serializers.CharField()
    tag = serializers.CharField(help_text=f'{MigrateTask.Tag.choices}')
