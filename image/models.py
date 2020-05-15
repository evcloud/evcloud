from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

from ceph.models import CephPool
from ceph.managers import get_rbd_manager, RadosError

User = get_user_model()
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
    TAG_BASE = 1
    TAG_USER = 2
    CHOICES_TAG = (
        (TAG_BASE, '基础镜像'),
        (TAG_USER, '用户镜像')
    )

    SYS_TYPE_WINDOWS = 1
    SYS_TYPE_LINUX = 2
    SYS_TYPE_UNIX = 3
    SYS_TYPE_MACOS = 4
    SYS_TYPE_ANDROID = 5
    SYS_TYPE_OTHER = 6  # 其他
    CHOICES_SYS_TYPE = (
        (SYS_TYPE_WINDOWS, 'Windows'),
        (SYS_TYPE_LINUX, 'Linux'),
        (SYS_TYPE_UNIX, 'Unix'),
        (SYS_TYPE_MACOS, 'MacOS'),
        (SYS_TYPE_ANDROID, 'Android'),
        (SYS_TYPE_OTHER, '其他'),
    )

    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name='镜像名称', max_length=100)
    version = models.CharField(verbose_name='系统版本信息', max_length=100)
    type = models.ForeignKey(to=ImageType, on_delete=models.CASCADE, verbose_name='类型')
    ceph_pool = models.ForeignKey(to=CephPool, on_delete=models.CASCADE, verbose_name='CEPH存储后端')
    tag = models.SmallIntegerField(verbose_name='镜像标签', choices=CHOICES_TAG, default=TAG_USER)
    sys_type = models.SmallIntegerField(verbose_name='系统类型', choices=CHOICES_SYS_TYPE, default=SYS_TYPE_OTHER)
    base_image = models.CharField(verbose_name='镜像', max_length=200, default='', help_text='用于创建镜像快照')
    enable = models.BooleanField(verbose_name='启用', default=True, help_text="若取消复选框，用户创建虚拟机时无法看到该镜像")
    create_newsnap = models.BooleanField('更新模板', default=False, help_text='''选中该选项，保存时会基于基础镜像"
           "创建新快照（以当前时间作为快照名称）,更新操作系统模板。新建snap时请确保基础镜像处于关机状态！''')  # 这个字段不需要持久化存储，用于获取用户页面选择
    snap = models.CharField(verbose_name='当前生效镜像快照', max_length=200, default='', blank=True, editable=True)
    xml_tpl = models.ForeignKey(to=VmXmlTemplate, on_delete=models.CASCADE, verbose_name='xml模板',
                                help_text='使用此镜象创建虚拟机时要使用的XML模板，不同类型的镜像有不同的XML格式')
    user = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True, blank=True, related_name='images_set', verbose_name='创建者')
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    desc = models.TextField(verbose_name='描述', default='', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-id']
        verbose_name = '操作系统镜像'
        verbose_name_plural = '10_操作系统镜像'
        unique_together = ('name', 'version')

    @property
    def fullname(self):
        return f'{self.name} {self.version}'

    @property
    def tag_display(self):
        return self.get_tag_display()

    @property
    def sys_type_display(self):
        return self.get_sys_type_display()

    def save(self, *args, **kwargs):
        if self.create_newsnap:  # 选中创建snap复选框
            self._create_snap()

        super().save(*args, **kwargs)

    def _create_snap(self):
        '''
        从基image创建快照snap，
        :return:
            True    # success
            raise Exception   # failed
        :raises: raise Exception
        '''
        ceph_pool = self.ceph_pool
        if not ceph_pool:
            raise Exception('create_snap failed, can not get ceph_pool')
        pool_name = ceph_pool.pool_name
        config = ceph_pool.ceph
        if not config:
            raise Exception('create_snap failed, can not get ceph')

        snap_name = timezone.now().strftime("%Y%m%d_%H%M%S")
        self.create_newsnap = False
        try:
            rbd = get_rbd_manager(ceph=config, pool_name=pool_name)
            try:
                rbd.remove_snap(image_name=self.base_image, snap=self.snap)     # 删除旧快照
            except RadosError as e:
                pass
            rbd.create_snap(image_name=self.base_image, snap_name=snap_name, protected=True)
        except RadosError as e:
            raise Exception(f'create_snap error, {str(e)}')

        self.snap = snap_name
        return True

    def delete(self, using=None, keep_parents=False):
        self._remove_image()
        super().delete(using=using, keep_parents=keep_parents)

    def _remove_image(self):
        '''
        删除image，需先删除其快照。（基础镜像不删除rbd image，基础镜像rbd image由管理员手动处理）
        :return:
            True    # success
            raise Exception   # failed
        :raises: raise Exception
        '''
        ceph_pool = self.ceph_pool
        if not ceph_pool:
            raise Exception('create_snap failed, can not get ceph_pool')
        pool_name = ceph_pool.pool_name
        config = ceph_pool.ceph
        if not config:
            raise Exception('create_snap failed, can not get ceph')

        try:
            rbd = get_rbd_manager(ceph=config, pool_name=pool_name)
            rbd.remove_snap(image_name=self.base_image, snap_name=self.snap)
            if self.tag != self.TAG_BASE:
                rbd.remove_image(image_name=self.base_image)
        except (RadosError, Exception) as e:
            raise Exception(f'remove snap or image error, {str(e)}')

        return True
