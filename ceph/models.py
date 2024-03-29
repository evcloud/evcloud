import os

from django.db import models
from django.conf import settings

from compute.models import Center
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


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
        verbose_name = _('CEPH集群')
        verbose_name_plural = _('03_CEPH集群')

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
            os.makedirs(path, exist_ok=True)

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
        verbose_name = 'CEPH Pool'
        verbose_name_plural = '04_CEPH Pool'

    def __str__(self):
        return f'ceph<{self.ceph.name}>@pool<{self.pool_name}>'


class GlobalConfig(models.Model):
    """全局配置表"""

    INSTANCE_ID = 1
    id = models.AutoField(primary_key=True, default=INSTANCE_ID)
    sitename = models.CharField(verbose_name=_('站点名称'), max_length=50, default='EVcloud')
    poweredby = models.CharField(verbose_name=_('技术支持'), max_length=255, default='https://gitee.com/cstcloud-cnic/evcloud')
    novnchttp = models.CharField(verbose_name=_('novnc http协议配置'), max_length=10, default='http',
                                 help_text=_('配置novnchttp协议 http/https'))

    class Meta:
        db_table = 'site_global_config'
        ordering = ['-id']
        verbose_name = _('全局配置表')
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'GlobalConfig<{self.sitename}>'

    @classmethod
    def get_instance(cls):
        inst = cls.objects.filter(id=cls.INSTANCE_ID).first()
        if not inst:
            return None

        return inst

    def save(self, *args, **kwargs):

        self.delete_global_config_cache()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # 删除缓存
        self.delete_global_config_cache()

        super().delete(*args, **kwargs)

    def clean(self):
        if self.novnchttp not in ['http', 'https']:
            raise ValidationError({'novnchttp': _('novnc http协议配置有误。')})

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