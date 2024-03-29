from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from compute.models import Center, Group
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

User = get_user_model()


class Vlan(models.Model):
    """
    虚拟局域网子网模型
    """
    NET_TAG_PRIVATE = 0
    NET_TAG_PUBLIC = 1
    NET_TAG_CHOICES = (
        (NET_TAG_PRIVATE, _('私网')),
        (NET_TAG_PUBLIC, _('公网'))
    )

    id = models.AutoField(primary_key=True)
    br = models.CharField(verbose_name=_('网桥名'), max_length=50)
    vlan_id = models.IntegerField(verbose_name=_('vlan id'), blank=True, null=True, default=None, validators=[MinValueValidator(0)])
    name = models.CharField(verbose_name=_('VLAN描述'), max_length=100)
    group = models.ForeignKey(to=Group, verbose_name=_('宿主机组'), default=None, null=True,
                              on_delete=models.SET_NULL, related_name='vlan_set')
    tag = models.SmallIntegerField(verbose_name=_('网络标签'), choices=NET_TAG_CHOICES, default=NET_TAG_PRIVATE)
    subnet_ip = models.GenericIPAddressField(verbose_name=_('子网IP'))
    net_mask = models.GenericIPAddressField(verbose_name=_('子网掩码'))
    gateway = models.GenericIPAddressField(verbose_name=_('网关'))
    dns_server = models.CharField(verbose_name=_('DNS服务IP'), max_length=255)
    subnet_ip_v6 = models.GenericIPAddressField(verbose_name=_('子网IP(IPv6)'), null=True, blank=True, default=None)
    net_mask_v6 = models.GenericIPAddressField(verbose_name=_('子网掩码(IPv6)'), null=True, blank=True, default=None)
    gateway_v6 = models.GenericIPAddressField(verbose_name=_('网关(IPv6)'), null=True, blank=True,  default=None)
    dns_server_v6 = models.CharField(verbose_name=_('DNS服务IP(IPv6)'), max_length=255, null=True, blank=True,  default=None)
    dhcp_config = models.TextField(verbose_name=_('DHCP部分配置信息'))
    dhcp_config_v6 = models.TextField(verbose_name=_('DHCP6部分配置信息'), null=True, blank=True,  default=None)
    enable = models.BooleanField(verbose_name=_('启用网络'), default=True)
    image_specialized = models.BooleanField(verbose_name=_('镜像虚拟机专用'), default=False)
    remarks = models.TextField(verbose_name=_('备注'), default='', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('id',)
        verbose_name = _('VLAN子网')
        verbose_name_plural = _('05_VLAN子网')

    def get_free_ip_number(self):
        """
        获得该子网已经生成，但尚未使用的ip数量
        :return: int
        """
        return self.macips.filter(used=False, enable=True).count()

    def get_ip_number(self):
        """
        获得该子网已经生成的所有ip数量
        :return: int
        """
        return self.macips.filter(enable=True).count()

    @property
    def free_ip(self):
        free_ip_number = self.get_free_ip_number()
        ip_number = self.get_ip_number()
        return f'{free_ip_number}/{ip_number}'

    def is_public(self):
        """
        是否是公网子网
        """
        return self.tag == self.NET_TAG_PUBLIC

    @property
    def tag_display(self):
        return self.get_tag_display()

    def check_shield_vlan(self, user):
        shield_vlan = ShieldVlan.objects.filter(user_name_id=user.id, vlan_id__id=self.id).first()  # 屏蔽vlan
        if not shield_vlan:
            return None
        return shield_vlan


class ShieldVlan(models.Model):
    """
    对用户屏蔽vlan
    """
    id = models.AutoField(primary_key=True)
    user_name = models.ForeignKey(to=User, on_delete=models.SET_NULL, related_name='user_vlan_shield', null=True,
                                  verbose_name=_('用户'))
    vlan_id = models.ManyToManyField(to=Vlan, related_name='vlan_shield',
                                     blank=True, verbose_name=_('vlan'))

    class Meta:
        ordering = ('id',)
        verbose_name = _('对用户屏蔽vlan')
        verbose_name_plural = _('12_对用户屏蔽vlan')

    def get_user_name(self):
        return self.user_name.username

    def get_vlan_id(self):
        vlan_list = []
        for obj in self.vlan_id.all():
            vlan_list.append(obj.id)

        return vlan_list


class MacIP(models.Model):
    """
    IP地址模型

    分配给虚拟机的IP地址
    """
    id = models.AutoField(primary_key=True)
    vlan = models.ForeignKey(to=Vlan, on_delete=models.SET_NULL, related_name='macips',
                             null=True, verbose_name=_('VLAN子网'))   # IP所属的vlan局域子网
    mac = models.CharField(verbose_name=_('MAC地址'), max_length=17, unique=True)
    ipv4 = models.GenericIPAddressField(verbose_name=_('IP地址'), unique=True)
    ipv6 = models.GenericIPAddressField(verbose_name=_('IPv6地址'), null=True, blank=True, default='')
    used = models.BooleanField(verbose_name=_('被使用'), default=False, help_text='是否已分配给虚拟机使用')
    enable = models.BooleanField(verbose_name=_('开启使用'), default=True, help_text='是否可以被分配使用')
    desc = models.TextField(verbose_name=_('备注说明'), default='', blank=True)

    class Meta:
        ordering = ['id']
        verbose_name = _('MAC IP地址')
        verbose_name_plural = _('07_MAC IP地址')

    def __str__(self):
        return self.ipv4

    def get_detail_str(self):
        return f'id={self.id};mac={self.mac};ipv4={self.ipv4};'

    @property
    def host_uuid(self):
        return self.ip_vm.uuid

    def can_used(self):
        """
        是否是自由的，可被使用的
        :return:
            True: 可使用
            False: 已被使用，或未开启使用
        """
        if not self.used and self.enable:
            return True
        return False

    @classmethod
    def get_all_free_ip_in_vlan(cls, vlan_id: int):
        """
        获取一个vlan子网中 未被使用的 可分配的 所有ip
        :param vlan_id: 子网ID
        :return:
            QuerySet()
        """
        return cls.objects.filter(vlan=vlan_id, used=False, enable=True).all()

    def set_in_used(self, auto_commit=True):
        """
        设置ip被使用中

        :param auto_commit: True:立即更新到数据库；False: 不更新到数据库
        :return:
            True    # 成功
            False   # 失败
        """
        if not auto_commit:
            self.used = True
            return True

        try:
            r = self.objects.filter(id=self.id, used=False).update(used=True)  # 乐观锁方式,
        except Exception as e:
            return False
        if r > 0:  # 更新行数
            self.used = True
            return True

        return False

    def set_free(self, auto_commit=True):
        """
        释放ip

        :param auto_commit: True:立即更新到数据库；False: 不更新到数据库
        :return:
            True    # 成功
            False   # 失败
        """
        if self.used is False:
            return True

        self.used = False
        if not auto_commit:
            return True

        try:
            self.save(update_fields=['used'])
        except Exception as e:
            return False

        return True

    def xml_desc(self):
        desc = """
            <interface type='bridge'>
              <mac address='{mac}'/>
              <source bridge='{bridge}'/>
              <model type='virtio'/>
            </interface>
        """.format(mac=self.mac, bridge=self.vlan.br)
        return desc

    def get_attach_ip_vm(self):
        return self.attach_ip.vm.uuid