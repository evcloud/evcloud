from django.db import models
from django.utils import timezone

from ceph.models import CephPool
from ceph.managers import RbdManager, RadosError

# Create your models here.

class VmXmlTemplate(models.Model):
    '''
    创建虚拟机的XML模板
    '''
    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name='模板名称', max_length=100, unique=True)
    xml = models.TextField(verbose_name='XML模板')
    desc = models.TextField(verbose_name='描述', default='', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '虚拟机XML模板'
        verbose_name_plural = '08_虚拟机XML模板'


class ImageType(models.Model):
    '''
    镜像镜像类型
    '''
    id = models.AutoField(primary_key=True)
    name = models.CharField('类型名称', max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '镜像分类'
        verbose_name_plural = '09_镜像分类'


class Image(models.Model):
    '''
    操作系统镜像
    '''
    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name='镜像名称', max_length=100)
    version = models.CharField(verbose_name='系统版本信息', max_length=100)
    type = models.ForeignKey(to=ImageType, on_delete=models.CASCADE, verbose_name='类型')
    ceph_pool = models.ForeignKey(to=CephPool, on_delete=models.CASCADE, verbose_name='CEPH存储后端')
    base_image = models.CharField(verbose_name='父镜像', max_length=200, default='', help_text='用于创建镜像快照')
    enable = models.BooleanField(verbose_name='启用', default=True, help_text="若取消复选框，用户创建虚拟机时无法看到该镜像")
    create_newsnap = models.BooleanField('更新模板', default=False, help_text='''选中该选项，保存时会基于基础镜像"
           "创建新快照（以当前时间作为快照名称）,更新操作系统模板。新建snap时请确保基础镜像处于关机状态！''')  # 这个字段不需要持久化存储，用于获取用户页面选择
    snap = models.CharField(verbose_name='当前生效镜像快照', max_length=200, default='', blank=True, editable=True)
    xml_tpl = models.ForeignKey(to=VmXmlTemplate, on_delete=models.CASCADE, verbose_name='xml模板',
                                help_text='使用此镜象创建虚拟机时要使用的XML模板，不同类型的镜像有不同的XML格式')
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    desc = models.TextField(verbose_name='描述', default='', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '操作系统镜像'
        verbose_name_plural = '10_操作系统镜像'
        unique_together = ('name', 'version')

    @property
    def fullname(self):
        return f'{self.name} {self.version}'

    def save(self, *args, **kwargs):
        # super().save(*args, **kwargs)
        if self.create_newsnap:  # 用户选中创建snap复选框
            self._create_snap()

        super().save(*args, **kwargs)

    def _create_snap(self):
        '''
        从基image创建快照snap，
        :return:
            True    # success
            False   # failed
        '''
        ceph_pool = self.ceph_pool
        if not ceph_pool:
            return False
        pool_name = ceph_pool.pool_name
        config = ceph_pool.ceph
        if not config:
            return False

        config_file = config.get_config_file()
        keyring_file = config.get_keyring_file()

        now_timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        snap_name = f'{self.base_image}@{now_timestamp}'
        self.create_newsnap = False
        try:
            rbd = RbdManager(conf_file=config_file, keyring_file=keyring_file, pool_name=pool_name)
            rbd.create_snap(image_name=self.base_image, snap_name=snap_name)
        except RadosError as e:
            self.enable = False
            self.desc = f'创建快照{snap_name}失败：{str(e)}' + self.desc
        except Exception as e:
            self.enable = False
            self.desc = f'创建快照{snap_name}失败：{str(e)}' + self.desc
        else:
            self.snap = snap_name
            return True

        return False

