import os

from django.db import models
from django.conf import settings

from compute.models import Center

# Create your models here.

class CephCluster(models.Model):
    '''
    Ceph集群相关配置信息的模型
    '''
    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name='名称', max_length=100, unique=True)
    center = models.ForeignKey(to=Center, on_delete=models.CASCADE, verbose_name='所属分中心', related_name='ceph_clusters')
    has_auth = models.BooleanField(verbose_name='是否需要认证', default=True, help_text='未选中时，不使用uuid字段，uuid设置为空')
    uuid = models.CharField(verbose_name='xml中ceph的uuid', max_length=50, blank=True, help_text='xml中ceph配置的uuid,libvirt通过uuid获取访问ceph的用户key')
    config = models.TextField(verbose_name='ceph集群配置文本', default='')
    config_file = models.CharField(max_length=200, editable=False, blank=True, verbose_name='配置文件保存路径', help_text="点击保存，配置文本会存储到这个文件, 此字段自动填充")
    keyring = models.TextField(verbose_name='ceph集群keyring文本')
    keyring_file = models.CharField(max_length=200, editable=False, blank=True, verbose_name='keyring文件保存路径', help_text="点击保存，keyring文本会存储到这个文件, 此字段自动填充")
    hosts_xml = models.TextField(verbose_name='ceph monitors', null=True, help_text="设置虚机xml中disk/source元素的ceph monitors信息，格式:&lt;host name='10.100.50.1' port='6789'/&gt;")
    username = models.CharField(verbose_name='ceph用户名', max_length=100, default='admin', help_text="ceph用户名，需与keyring文件一致")

    class Meta:
        ordering = ('id',)
        verbose_name = 'CEPH集群'
        verbose_name_plural = '03_CEPH集群'

    def __str__(self):
        return self.name

    def get_config_file(self):
        '''
        ceph配置文件路径
        :return: str
        '''
        if not self.config_file:
            self._save_config_to_file()

        return self.config_file

    def get_keyring_file(self):
        '''
        ceph keyring文件路径
        :return: str
        '''
        if not self.keyring_file:
            self._save_config_to_file()

        return self.keyring_file

    def _save_config_to_file(self):
        '''
        ceph的配置内容保存到配置文件

        :return:
            True    # success
            False   # failed
        '''
        path = os.path.join(settings.BASE_DIR, 'data/ceph/conf/')
        self.config_file = os.path.join(path, f'{self.id}.conf')
        self.keyring_file = os.path.join(path, f'{self.id}.keyring')

        try:
            # 目录路径不存在存在则创建
            os.makedirs(path, exist_ok=True)

            with open(self.config_file, 'w') as f:
                f.write(self.config)

            with open(self.keyring_file, 'w') as f:
                f.write(self.keyring)
        except Exception:
            return False

        return True

    def save(self, *args, **kwargs):
        if not self.id:
            super().save(*args, **kwargs)

        self._save_config_to_file()
        super().save(*args, **kwargs)


class CephPool(models.Model):
    '''
    CEPH pool
    '''
    id = models.AutoField(primary_key=True)
    pool_name = models.CharField(verbose_name='POOL名称', max_length=100)
    has_data_pool = models.BooleanField(default=False, verbose_name='是否有独立存储POOL')
    data_pool = models.CharField(verbose_name='数据存储POOL名称', max_length=100, blank=True, default='')
    ceph = models.ForeignKey(to=CephCluster, on_delete=models.CASCADE)
    enable = models.BooleanField(default=True, verbose_name='是否启用')
    remarks = models.CharField(max_length=255, default='', blank=True, verbose_name='备注')

    class Meta:
        ordering = ('id',)
        verbose_name = 'CEPH Pool'
        verbose_name_plural = '04_CEPH Pool'

    def __str__(self):
        return f'ceph<{self.ceph.name}>@pool<{self.pool_name}>'


