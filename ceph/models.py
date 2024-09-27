import ipaddress
import os

from django.db import models
from django.conf import settings

from compute.models import Center
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from utils.iprestrict import convert_iprange


class CephCluster(models.Model):
    """
    Ceph集群相关配置信息的模型
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name=_('名称'), max_length=100, unique=True)
    center = models.ForeignKey(to=Center, on_delete=models.CASCADE, verbose_name=_('所属数据中心'), related_name='ceph_clusters')
    has_auth = models.BooleanField(verbose_name=_('需要认证'), default=True, help_text=_('未选中时，不使用uuid字段，uuid设置为空'))
    uuid = models.CharField(verbose_name=_('xml中ceph的uuid'), max_length=50, blank=True,
                            help_text=_('xml中ceph配置的uuid,libvirt通过uuid获取访问ceph的用户key'))
    config = models.TextField(verbose_name=_('ceph集群配置文本'), default='')
    config_file = models.CharField(max_length=200, editable=False, blank=True, verbose_name=_('配置文件保存路径'),
                                   help_text=_("点击保存，配置文本会存储到这个文件, 此字段自动填充"))
    keyring = models.TextField(verbose_name=_('ceph集群keyring文本'))
    keyring_file = models.CharField(max_length=200, editable=False, blank=True, verbose_name=_('keyring文件保存路径'),
                                    help_text=_("点击保存，keyring文本会存储到这个文件, 此字段自动填充"))
    hosts_xml = models.TextField(verbose_name='ceph monitors', null=True,
                                 help_text=_("设置虚机xml中disk/source元素的ceph monitors信息，"
                                            "格式:&lt;host name='10.100.50.1' port='6789'/&gt;"))
    username = models.CharField(verbose_name=_('ceph用户名'), max_length=100, default='admin',
                                help_text=_("ceph用户名，需与keyring文件一致"))

    class Meta:
        ordering = ('id',)
        verbose_name = _('CEPH存储集群')
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

    def get_config_file(self):
        """
        ceph配置文件路径
        :return: str
        """
        if not self.config_file:
            self._save_config_to_file()

        return self.config_file

    def get_keyring_file(self):
        """
        ceph keyring文件路径
        :return: str
        """
        if not self.keyring_file:
            self._save_config_to_file()

        return self.keyring_file

    def _save_config_to_file(self):
        """
        ceph的配置内容保存到配置文件

        :return:
            True    # success
            False   # failed
        """
        path = os.path.join(settings.BASE_DIR, 'data/ceph/conf/')
        self.config_file = os.path.join(path, f'{self.id}.conf')
        self.keyring_file = os.path.join(path, f'{self.id}.keyring')

        try:
            # 目录路径不存在存在则创建
            os.makedirs(path, exist_ok=True, mode=0o755)  # 目录权限 755

            with open(self.config_file, 'w') as f:
                config = self.config.replace('\r\n', '\n')      # Windows
                self.config = config.replace('\r', '\n')        # MacOS
                f.write(self.config + '\n')     # 最后留空行

            with open(self.keyring_file, 'w') as f:
                keyring = self.keyring.replace('\r\n', '\n')
                self.keyring = keyring.replace('\r', '\n')
                f.write(self.keyring + '\n')
        except Exception:
            return False

        os.chmod(self.config_file, 0o644)  # 设置权限
        os.chmod(self.keyring_file, 0o644)  # 设置权限
        return True

    def save(self, *args, **kwargs):
        if not self.id:
            super().save(*args, **kwargs)

        self._save_config_to_file()
        super().save(*args, **kwargs)


class CephPool(models.Model):
    """
    CEPH pool
    """
    id = models.AutoField(primary_key=True)
    pool_name = models.CharField(verbose_name=_('POOL名称'), max_length=100)
    has_data_pool = models.BooleanField(default=False, verbose_name=_('具备独立存储POOL'))
    data_pool = models.CharField(verbose_name=_('数据存储POOL名称'), max_length=100, blank=True, default='')
    ceph = models.ForeignKey(to=CephCluster, on_delete=models.CASCADE)
    enable = models.BooleanField(default=True, verbose_name=_('启用存储POOL'))
    remarks = models.CharField(max_length=255, default='', blank=True, verbose_name=_('备注'))

    class Meta:
        ordering = ('id',)
        verbose_name = _('CEPH数据存储池')
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'ceph<{self.ceph.name}>@pool<{self.pool_name}>'


class GlobalConfig(models.Model):
    """全局配置表-站点参数"""

    id = models.AutoField(primary_key=True, verbose_name=_('ID'))
    name = models.CharField(verbose_name=_('名称'), max_length=255)
    content = models.TextField(verbose_name=_('内容'), default='', null=True, blank=True)
    remark = models.CharField(verbose_name=_('备注信息'), max_length=255, default='', blank=True)
    create_time = models.DateTimeField(verbose_name=_('创建时间'), auto_now_add=True)
    modif_time = models.DateTimeField(verbose_name=_('修改时间'), auto_now=True)

    class Meta:
        db_table = 'site_global_config'
        ordering = ['-id']
        verbose_name = _('站点参数')
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'GlobalConfig<{self.name}>'

    @classmethod
    def create_base_data(cls, name, content, remark):
        """写入基数据"""
        obj = cls.objects.filter(name=name).first()
        if not obj:
            cls.objects.get_or_create(name=name, content=content, remark=remark)

        return

    def initial_site_parameter(self):
        """初始站点化参数"""
        parameter_list = [
            {'name': 'siteName', 'content': 'EVCloud', 'remark': '站点名称'},
            {'name': 'poweredBy', 'content': 'https://gitee.com/cstcloud-cnic/evcloud', 'remark': '技术支持'},
            {'name': 'novncAccess', 'content': 'https', 'remark': 'vnc http协议'},
            {'name': 'resourceAdmin', 'content': 'gosc,cstcloud', 'remark': '资源管理员，格式：admin1,admin2...'},
            {'name': 'vpnUserConfig', 'content': '', 'remark': 'vpn配置文件'},
            {'name': 'vpnUserConfigDownloadName', 'content': 'client.ovpn', 'remark': 'vpn配置文件下载名称。'},
        ]

        for param in parameter_list:
            self.create_base_data(name=param['name'], content=param['content'], remark=param['remark'])

        return

    @classmethod
    def get_instance(cls):
        inst_dict = {}
        inst = cls.objects.filter(name__in=['siteName', 'poweredBy', 'novncAccess'])
        if not inst:
            inst_dict['siteName'] = 'EVCloud'
            inst_dict['poweredBy'] = 'https://gitee.com/cstcloud-cnic/evcloud'
            inst_dict['novncAccess'] = 'https'
            return inst_dict

        for obj in inst:
            if obj.name == 'siteName':
                inst_dict['siteName'] = obj.content
            elif obj.name == 'poweredBy':
                inst_dict['poweredBy'] = obj.content
            elif obj.name == 'novncAccess':
                inst_dict['novncAccess'] = obj.content

        return inst_dict

    def save(self, *args, **kwargs):

        self.delete_global_config_cache()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # 删除缓存
        self.delete_global_config_cache()

        super().delete(*args, **kwargs)

    @staticmethod
    def get_global_config():
        global_config = cache.get('global_config_key')
        if global_config:
            return global_config

        obj = GlobalConfig.get_instance()
        cache.set('global_config_key', obj, 120)

        return cache.get('global_config_key')

    @staticmethod
    def delete_global_config_cache():
        cache.delete('global_config_key')


class ApiAllowIP(models.Model):
    """全局配置表-管理员IP白名单：配置 nginx 允许的IP"""
    id = models.BigAutoField(primary_key=True)
    ip_value = models.CharField(
        verbose_name=_('IP'), max_length=100, help_text='192.168.1.1、 192.168.1.1/24、192.168.1.66 - 192.168.1.100')
    remark = models.CharField(verbose_name=_('备注'), max_length=255, blank=True, default='')
    creation_time = models.DateTimeField(verbose_name=_('创建时间'), auto_now_add=True)
    update_time = models.DateTimeField(verbose_name=_('更新时间'), auto_now=True)

    class Meta:
        db_table = 'app_global_parameter_apiallowip' # 后续 app 更名为 app_global_parameter
        ordering = ['-creation_time']
        verbose_name = _('IP访问白名单')
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.id}({self.ip_value})'

    def clean(self):
        try:
            subnet = convert_iprange(self.ip_value)
        except Exception as exc:
            raise ValidationError({'ip_value': str(exc)})

        if isinstance(subnet, ipaddress.IPv4Network):
            self.ip_value = str(subnet)
