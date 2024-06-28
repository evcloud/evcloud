import math

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from logrecord.models import LogRecord
from vms.models import Vm, MigrateTask, AttachmentsIP
from compute.models import Center, Group, Host
from network.models import Vlan
from image.models import Image, MirrorImageTask, VmXmlTemplate
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
        fields = (
            'uuid', 'name', 'vcpu', 'mem', 'image', 'disk', 'sys_disk_size', 'host', 'mac_ip', 'ip', 'user',
            'create_time')
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
        return {'ipv4': obj.mac_ip.ipv4, 'public_ipv4': public, 'ipv6': obj.mac_ip.ipv6}

    @staticmethod
    def get_image(obj):
        return obj.image_name

    def to_representation(self, instance):
        """Convert `GB` to 'MB' depending on the requirement."""
        ret = super().to_representation(instance)
        if 'GB' == self.context.get('mem_unit'):
            ret['mem_unit'] = 'GB'
        else:
            ret['mem'] = ret['mem'] * 1024
            ret['mem_unit'] = 'MB'
        return ret


class VmCreateSerializer(serializers.Serializer):
    """
    创建虚拟机序列化器
    """
    image_id = serializers.IntegerField(label='镜像id', required=True, min_value=1, help_text='系统镜像id')
    vcpu = serializers.IntegerField(label='cpu数', min_value=1, required=False,
                                    allow_null=True, default=None, help_text='cpu数')
    mem = serializers.IntegerField(label='内存大小', min_value=1, required=False,
                                   allow_null=True, default=None, help_text='单位GB')
    vlan_id = serializers.IntegerField(label='子网id', required=False, allow_null=True,
                                       min_value=1, help_text='子网id', default=None)
    center_id = serializers.IntegerField(label='数据中心id', required=False, allow_null=True,
                                         min_value=1, help_text='数据中心id', default=None)
    group_id = serializers.IntegerField(label='宿主机组id', required=False, allow_null=True,
                                        min_value=1, help_text='宿主机组id', default=None)
    host_id = serializers.IntegerField(label='宿主机id', required=False, allow_null=True,
                                       min_value=1, help_text='宿主机id', default=None)
    remarks = serializers.CharField(label='备注', required=False, allow_blank=True, max_length=255, default='')
    ipv4 = serializers.CharField(label='ipv4', required=False, allow_blank=True, max_length=255, default='')
    flavor_id = serializers.IntegerField(label='配置样式id', required=False, allow_null=True,
                                         default=None, help_text='配置样式id')
    sys_disk_size = serializers.IntegerField(label='系统盘大小', min_value=50, max_value=5 * 1024, required=False,
                                             allow_null=True, default=None, help_text='单位GB')

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

    def to_internal_value(self, instance):
        """Convert `MB` to 'GB' if mem_unit is 'MB' or null."""
        ret = super().to_internal_value(instance)
        if 'GB' == self.context.get('mem_unit'):
            pass
        else:
            ret['mem'] = math.ceil(ret['mem'] / 1024)
        return ret


class VmPatchSerializer(serializers.Serializer):
    """
    创建虚拟机序列化器
    """
    flavor_id = serializers.IntegerField(label='配置样式id', required=False, allow_null=True, default=None,
                                         help_text='配置样式id')
    vcpu = serializers.IntegerField(label='cpu数', min_value=1, required=False, allow_null=True, default=0,
                                    help_text='cpu数')
    mem = serializers.IntegerField(label='内存大小', min_value=1, required=False, allow_null=True, default=0,
                                   help_text='单位GB')

    def validate(self, data):
        vcpu = data.get('vcpu')
        mem = data.get('mem')
        flavor_id = data.get('flavor_id')

        if (not flavor_id) and (not vcpu and not mem):
            raise serializers.ValidationError(detail={'code_text': '必须提交flavor_id或者直接指定vcp或mem)'})
        return data

    def to_internal_value(self, instance):
        """Convert `MB` to 'GB' if mem_unit is 'MB' or null."""
        ret = super().to_internal_value(instance)
        if 'GB' == self.context.get('mem_unit'):
            pass
        else:
            ret['mem'] = math.ceil(ret['mem'] / 1024)
        return ret


class CenterSerializer(serializers.ModelSerializer):
    """
    数据中心序列化器
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
                  'vm_limit', 'vm_created', 'enable', 'desc')

    def to_representation(self, instance):
        """Convert `GB` to 'MB' depending on the requirement."""
        ret = super().to_representation(instance)
        if 'GB' == self.context.get('mem_unit'):
            ret['mem_unit'] = 'GB'
        else:
            ret['mem_total'] = ret['mem_total'] * 1024
            ret['mem_allocated'] = ret['mem_allocated'] * 1024
            ret['mem_unit'] = 'MB'
        return ret


class VlanSerializer(serializers.ModelSerializer):
    """
    子网网段序列化器
    """

    class Meta:
        model = Vlan
        fields = ('id', 'name', 'br', 'tag', 'enable', 'subnet_ip', 'net_mask', 'gateway', 'dns_server', 'subnet_ip_v6',
                  'net_mask_v6', 'gateway_v6', 'dns_server_v6', 'remarks')


class ImageSerializer(serializers.ModelSerializer):
    """
    子网网段序列化器
    """
    tag = serializers.SerializerMethodField()
    sys_type = serializers.SerializerMethodField()
    release = serializers.SerializerMethodField()
    architecture = serializers.SerializerMethodField()
    create_time = serializers.DateTimeField()

    class Meta:
        model = Image
        fields = (
            'id', 'name', 'tag', 'sys_type', 'release', 'version', 'architecture', 'enable', 'create_time', 'desc',
            'default_user', 'default_password', 'size')

    @staticmethod
    def get_tag(obj):
        return {'id': obj.tag, 'name': obj.tag_display}

    @staticmethod
    def get_sys_type(obj):
        return {'id': obj.sys_type, 'name': obj.sys_type_display}

    @staticmethod
    def get_release(obj):
        return {'id': obj.release, 'name': obj.release_display}

    @staticmethod
    def get_architecture(obj):
        return {'id': obj.architecture, 'name': obj.architecture_display}


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

        return {'id': pool.id, 'name': pool.pool_name, 'enable': obj.enable}

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
    enable = serializers.BooleanField()


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
            return {'uuid': vm.hex_uuid, 'ipv4': vm.mac_ip.ipv4, 'ipv6': vm.mac_ip.ipv6}
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
        fields = ('uuid', 'size', 'vm', 'dev', 'user', 'quota', 'create_time', 'attach_time', 'enable', 'remarks')
        depth = 1

    @staticmethod
    def get_vm(obj):
        vm = obj.vm
        if vm:
            if vm.mac_ip:
                return {'uuid': vm.hex_uuid, 'ipv4': vm.mac_ip.ipv4, 'ipv6': vm.mac_ip.ipv6}
            return {'uuid': vm.hex_uuid, 'ipv4': ''}  # 搁置的虚拟机没有ip
        return vm

    @staticmethod
    def get_dev(obj):
        return {'dev': obj.dev}


class VdiskCreateSerializer(serializers.Serializer):
    """
    虚拟硬盘创建序列化器
    """
    size = serializers.IntegerField(label='容量大小（GB）', required=True, min_value=1, help_text='容量大小,单位GB')
    quota_id = serializers.IntegerField(label='硬盘存储池id', required=False, allow_null=True,
                                        min_value=1, help_text='宿主机组id', default=None)
    group_id = serializers.IntegerField(label='宿主机组id', required=False, allow_null=True,
                                        min_value=1, help_text='宿主机组id', default=None)
    center_id = serializers.IntegerField(label='数据中心id', required=False, allow_null=True,
                                         min_value=1, help_text='数据中心id', default=None)
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
            return {'uuid': vm.hex_uuid, 'ipv4': vm.mac_ip.ipv4, 'ipv6': vm.mac_ip.ipv6}
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
    ipv6 = serializers.IPAddressField(help_text='IPv6地址')
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
    host_info = serializers.SerializerMethodField()

    class Meta:
        model = Vm
        fields = ('uuid', 'name', 'vcpu', 'mem', 'image', 'image_info', 'disk', 'sys_disk_size', 'host', 'mac_ip',
                  'ip', 'user', 'create_time', 'vdisks', 'pci_devices', 'host_info', 'vm_status')
        # depth = 1

    @staticmethod
    def get_vm_status(obj):
        return obj.vm_status

    @staticmethod
    def get_user(obj):
        return {'id': obj.user.id, 'username': obj.user.username}

    @staticmethod
    def get_host(obj):
        if not obj.host:
            return 'null'
        return obj.host.ipv4

    @staticmethod
    def get_mac_ip(obj):
        if not obj.mac_ip:
            return 'null'
        return obj.mac_ip.ipv4

    @staticmethod
    def get_ip(obj):

        if not obj.mac_ip:
            return {'ipv4': 'null', 'public_ipv4': 'null'}
        elif obj.mac_ip.vlan:
            public = obj.mac_ip.vlan.tag == obj.mac_ip.vlan.NET_TAG_PUBLIC
        else:
            public = False
        return {'ipv4': obj.mac_ip.ipv4, 'public_ipv4': public, 'ipv6': obj.mac_ip.ipv6}

    @staticmethod
    def get_image(obj):
        return obj.image_name

    @staticmethod
    def get_image_info(obj):
        return {
            'id': obj.image_id, 'name': obj.image_name, 'desc': obj.image_desc,
            'default_user': obj.default_user, 'default_password': obj.default_password
        }

    @staticmethod
    def get_vdisks(obj):
        vdisks = obj.vdisks.select_related('quota__group', 'vm__mac_ip', 'user')
        return VdiskSerializer(instance=vdisks, many=True, required=False).data

    @staticmethod
    def get_pci_devices(obj):
        devs = obj.pci_devices.select_related('host__group', 'vm')
        return PCIDeviceSerializer(instance=devs, many=True, required=False).data

    @staticmethod
    def get_host_info(obj):
        host = obj.host
        if host:
            return {
                'id': host.id, 'ipv4': host.ipv4, 'group': {'id': host.group_id}
            }

        return None

    def to_representation(self, instance):
        """Convert `GB` to 'MB' depending on the requirement."""
        ret = super().to_representation(instance)
        if 'GB' == self.context.get('mem_unit'):
            ret['mem_unit'] = 'GB'
        else:
            ret['mem'] = ret['mem'] * 1024
            ret['mem_unit'] = 'MB'
        return ret


class VmShelveListSerializer(serializers.ModelSerializer):
    """
    虚拟机搁置序列化器
    """
    user = serializers.SerializerMethodField()  # 自定义user字段内容
    create_time = serializers.DateTimeField()  # format='%Y-%m-%d %H:%M:%S'
    image = serializers.SerializerMethodField()

    class Meta:
        model = Vm
        fields = (
            'uuid', 'name', 'vm_status', 'vcpu', 'mem', 'image', 'disk', 'sys_disk_size', 'host', 'mac_ip', 'user',
            'create_time')

    @staticmethod
    def get_vm_status(obj):
        return obj.vm_status

    @staticmethod
    def get_user(obj):
        return {'id': obj.user.id, 'username': obj.user.username}

    @staticmethod
    def get_image(obj):
        return obj.image_name

    def to_representation(self, instance):
        """Convert `GB` to 'MB' depending on the requirement."""
        ret = super().to_representation(instance)
        if 'GB' == self.context.get('mem_unit'):
            ret['mem_unit'] = 'GB'
        else:
            ret['mem'] = ret['mem'] * 1024
            ret['mem_unit'] = 'MB'
        return ret


class VmAttachListSerializer(serializers.ModelSerializer):
    """附加IP"""
    attach_ip = serializers.SerializerMethodField()

    class Meta:
        model = AttachmentsIP
        fields = ('id', 'vm', 'attach_ip')

    def get_attach_ip(self, obj):
        return obj.sub_ip.ipv4


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

    def to_representation(self, instance):
        """Convert `GB` to 'MB' depending on the requirement."""
        ret = super().to_representation(instance)
        if 'GB' == self.context.get('mem_unit'):
            ret['mem_unit'] = 'GB'
        else:
            ret['ram'] = ret['ram'] * 1024
            ret['mem_unit'] = 'MB'
        return ret


class VPNCreateSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, min_length=1, max_length=150)
    password = serializers.CharField(required=False, min_length=6, max_length=64, default='',
                                     help_text='如果未指定，随机分配密码')


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


class LogRecordSerializer(serializers.ModelSerializer):
    """用户操作日志"""
    create_time = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    operation_content = serializers.CharField()

    class Meta:
        model = LogRecord
        fields = ('create_time', 'username', 'operation_content')

    def get_create_time(self, obj):
        return obj.create_time.timestamp()

    def get_username(self, obj):
        if obj.real_user:
            return obj.real_user
        return obj.username


class VmXmlTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VmXmlTemplate
        fields = ('id', 'name', 'desc', 'max_cpu_socket')


class MirrorImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MirrorImageTask
        fields = ('id', 'mirror_image_name', 'mirror_image_sys_type', 'mirror_image_version', 'mirror_image_release',
                  'mirror_image_architecture', 'mirror_image_boot_mode', 'mirror_image_base_image',
                  'mirror_image_enable', 'mirror_image_xml_tpl', 'user', 'create_time', 'update_time', 'desc',
                  'mirror_image_default_user', 'mirror_image_default_password', 'mirror_image_size', 'operate',
                  'mirrors_image_service_url', 'status', 'import_date', 'import_date_complate',
                  'export_date', 'export_date_complate', 'error_msg', 'bucket_name', 'file_path', 'token')


class MirrorImageCreateSerializer(serializers.Serializer):
    mirrors_image_service_url = serializers.CharField(label=_('公共镜像地址'), required=True, max_length=255)
    bucket_name = serializers.CharField(label=_('存储桶名称'), required=True, max_length=255)
    file_path = serializers.CharField(label=_('文件路径'), required=True, max_length=255, help_text=_('完整路径'))
    token = serializers.CharField(label=_('存储桶token'), required=True, max_length=255)
    mirror_image_name = serializers.CharField(label=_('镜像名称'), required=True, max_length=255)
    mirror_image_base_image = serializers.CharField(label=_('镜像'), required=True, max_length=255,
                                                    help_text='导入ceph的镜像需要的名称与镜像名称不一样，如果不唯一就会报错')
    mirror_image_xml_tpl = serializers.IntegerField(label=_('xml模板'), required=True,
                                                    help_text=' 找到xml模板的数据,填写id')
    mirror_image_sys_type = serializers.CharField(label=_('系统类型'), required=False, max_length=255, default='Linux',
                                                  help_text='默认Linux :Windows、Linux、Unix、MacOS、Android、其他')
    mirror_image_version = serializers.CharField(label=_('系统发行编号'), required=False, max_length=255,
                                                 help_text='默认 stream 9', default='stream 9')
    mirror_image_release = serializers.CharField(label=_('系统发行版本'), required=False, max_length=255,
                                                 default='Centos',
                                                 help_text=' 默认Centos ：Centos、Ubuntu、Windows Desktop、Windows Server、Fedora、Rocky、Unknown')
    mirror_image_architecture = serializers.CharField(label=_('系统架构'), required=False, max_length=255,
                                                      help_text=' 默认x86-64 ：x86-64、i386、arm-64、unknown',
                                                      default='x86-64')
    mirror_image_boot_mode = serializers.CharField(label=_('系统启动方式'), required=False, max_length=255,
                                                   help_text='默认BIOS ：BIOS、UEFI', default='BIOS')
    mirror_image_enable = serializers.BooleanField(label=_('启用'), required=False, default=True,
                                                   help_text='镜像导入成功后，会启用镜像，否则不会启用')
    desc = serializers.CharField(label=_('描述'), required=False, max_length=255)
    mirror_image_default_user = serializers.CharField(label=_('系统默认登录用户名'), required=False, max_length=255,
                                                      default='xxx')
    mirror_image_default_password = serializers.CharField(label=_('系统默认登录密码'), required=False, max_length=255,
                                                          default='xxx', )
    mirror_image_size = serializers.IntegerField(label=_('镜像大小（Gb）'), required=False, default=0,
                                                 help_text='不是整Gb大小，要向上取整，如1.1GB向上取整为2Gb')

    def validate(self, data):
        file_path = data.get('file_path')
        mirrors_image_service_url = data.get('mirrors_image_service_url')

        if not file_path:
            raise serializers.ValidationError(detail={'file_path': '必须填写的参数， 格式/xxx/xxx.qcow2'})

        if not file_path.endswith('.qcow2'):
            raise serializers.ValidationError(detail={'file_path': '格式/xxx/xxx.qcow2'})

        return data
