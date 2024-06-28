import math

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from ceph.models import CephPool
from ceph.managers import get_rbd_manager, RadosError
from compute.models import Host
from network.models import MacIP

User = get_user_model()


class VmXmlTemplate(models.Model):
    """
    创建虚拟机的XML模板
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name=_('模板名称'), max_length=100, unique=True)
    xml = models.TextField(verbose_name=_('XML模板'))
    desc = models.TextField(verbose_name=_('描述'), default='', blank=True)
    max_cpu_socket = models.IntegerField(verbose_name=('cpu 颗数'), default=0, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('虚拟机XML模板')
        verbose_name_plural = _('08_虚拟机XML模板')


class Image(models.Model):
    """
    操作系统镜像
    """
    TAG_BASE = 1
    TAG_USER = 2
    CHOICES_TAG = (
        (TAG_BASE, _('基础镜像')),
        (TAG_USER, _('用户镜像'))
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
        (SYS_TYPE_OTHER, _('其他')),
    )

    RELEASE_WINDOWS_DESKTOP = 1
    RELEASE_WINDOWS_SERVER = 2
    RELEASE_UBUNTU = 3
    RELEASE_FEDORA = 4
    RELEASE_CENTOS = 5
    RELEASE_UNKNOWN = 6
    RELEASE_ROCKY = 7
    RELEASE_CHOICES = (
        (RELEASE_WINDOWS_DESKTOP, 'Windows Desktop'),
        (RELEASE_WINDOWS_SERVER, 'Windows Server'),
        (RELEASE_UBUNTU, 'Ubuntu'),
        (RELEASE_FEDORA, 'Fedora'),
        (RELEASE_CENTOS, 'Centos'),
        (RELEASE_ROCKY, 'Rocky'),
        (RELEASE_UNKNOWN, 'Unknown'),
    )

    ARCHITECTURE_X86_64 = 1
    ARCHITECTURE_I386 = 2
    ARCHITECTURE_ARM_64 = 3
    ARCHITECTURE_UNKNOWN = 4
    ARCHITECTURE_CHOICES = (
        (ARCHITECTURE_X86_64, 'x86-64'),
        (ARCHITECTURE_I386, 'i386'),
        (ARCHITECTURE_ARM_64, 'arm-64'),
        (ARCHITECTURE_UNKNOWN, 'unknown'),
    )

    BOOT_UEFI = 1
    BOOT_BIOS = 2
    BOOT_CHOICES = (
        (BOOT_UEFI, 'UEFI'),
        (BOOT_BIOS, 'BIOS'),
    )

    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name=_('镜像名称'), max_length=100)
    sys_type = models.SmallIntegerField(verbose_name=_('系统类型'), choices=CHOICES_SYS_TYPE, default=SYS_TYPE_OTHER)
    version = models.CharField(verbose_name=_('系统发行编号'), max_length=100)
    release = models.SmallIntegerField(verbose_name=_('系统发行版本'), choices=RELEASE_CHOICES, default=RELEASE_CENTOS)
    architecture = models.SmallIntegerField(verbose_name=_('系统架构'), choices=ARCHITECTURE_CHOICES,
                                            default=ARCHITECTURE_X86_64)
    boot_mode = models.SmallIntegerField(verbose_name=_('系统启动方式'), choices=BOOT_CHOICES, default=BOOT_BIOS)
    nvme_support = models.BooleanField(verbose_name=_('支持NVME设备'), default=False)

    ceph_pool = models.ForeignKey(to=CephPool, on_delete=models.CASCADE, verbose_name=_('CEPH存储后端'))
    tag = models.SmallIntegerField(verbose_name=_('镜像标签'), choices=CHOICES_TAG, default=TAG_USER)
    base_image = models.CharField(verbose_name=_('镜像'), max_length=200, default='', help_text='用于创建镜像快照')
    enable = models.BooleanField(verbose_name=_('启用'), default=True,
                                 help_text="若取消复选框，用户创建虚拟机时无法看到该镜像")
    snap = models.CharField(verbose_name=_('当前生效镜像快照'), max_length=200, default='', blank=True, editable=True)
    xml_tpl = models.ForeignKey(to=VmXmlTemplate, on_delete=models.CASCADE, verbose_name=_('xml模板'),
                                help_text='使用此镜象创建虚拟机时要使用的XML模板，不同类型的镜像有不同的XML格式')
    user = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='images_set', verbose_name=_('创建者'))
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    desc = models.TextField(verbose_name=_('描述'), default='', blank=True)
    default_user = models.CharField(verbose_name=_('系统默认登录用户名'), max_length=32, default='root')
    default_password = models.CharField(verbose_name=_('系统默认登录密码'), max_length=32, default='cnic.cn')
    size = models.IntegerField(verbose_name=_('镜像大小（Gb）'), default=0,
                               help_text='image size不是整Gb大小，要向上取整，如1.1GB向上取整为2Gb')
    vm_host = models.ForeignKey(to=Host, on_delete=models.SET_NULL, verbose_name=_('宿主机'), null=True, blank=True,
                                default=None)
    vm_uuid = models.CharField(verbose_name=_('虚拟机UUID'), max_length=36, null=True, blank=True, )
    vm_mac_ip = models.ForeignKey(to=MacIP, on_delete=models.SET_NULL, verbose_name=_('MAC IP'), null=True,
                                  blank=True, )
    vm_vcpu = models.IntegerField(verbose_name=_('CPU数'), null=True, blank=True, )
    vm_mem = models.IntegerField(verbose_name=_('内存大小'), help_text='单位GB', null=True, blank=True, )

    mirror_image_market = models.BooleanField(verbose_name=_('镜像市场'), help_text='镜像市场下载的镜像', default=False)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-id']
        verbose_name = _('操作系统镜像')
        verbose_name_plural = _('10_操作系统镜像')
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

    @property
    def release_display(self):
        return self.get_release_display()

    @property
    def architecture_display(self):
        return self.get_architecture_display()

    def save(self, *args, **kwargs):
        if not self.pk:  # 如果新增系统镜像
            self._create_image_if_not_exist()
            if not self.snap:  # 如果没有快照就创建
                self.create_snap()
        super().save(*args, **kwargs)

    def _create_image_if_not_exist(self):
        """
        若不存在rbd镜像则创建空的rbd镜像，
        :return:
            True    # 创建镜像
            raise Exception   # 未创建镜像
        :raises: raise Exception
        """
        ceph_pool = self.ceph_pool
        if not ceph_pool:
            raise Exception('create_snap failed, can not get ceph_pool')
        pool_name = ceph_pool.pool_name
        config = ceph_pool.ceph
        if not config:
            raise Exception('create_snap failed, can not get ceph')
        try:
            if self.size is not None:
                image_size = self.size * 1024 ** 3
            else:
                image_size = 40 * 1024 ** 3
            rbd = get_rbd_manager(ceph=config, pool_name=pool_name)
            if not rbd.image_exists(self.base_image):
                rbd.create_image(name=self.base_image, size=image_size, data_pool=pool_name)
                return True
        except RadosError as e:
            raise Exception(f'create_image_if_not_exist error, {str(e)}')
        return False

    def create_snap(self):
        """
        从基image创建快照snap，
        :return:
            True    # success
            raise Exception   # failed
        :raises: raise Exception
        """
        ceph_pool = self.ceph_pool
        if not ceph_pool:
            raise Exception('create_snap failed, can not get ceph_pool')
        pool_name = ceph_pool.pool_name
        config = ceph_pool.ceph
        if not config:
            raise Exception('create_snap failed, can not get ceph')

        snap_name = timezone.now().strftime("%Y%m%d_%H%M%S")
        try:
            rbd = get_rbd_manager(ceph=config, pool_name=pool_name)
            try:
                rbd.remove_snap(image_name=self.base_image, snap=self.snap)  # 删除旧快照
            except RadosError as e:
                pass
            rbd.create_snap(image_name=self.base_image, snap_name=snap_name, protected=True)
        except RadosError as e:
            raise Exception(f'create_snap error, {str(e)}')
        self.snap = snap_name
        return True

    def delete(self, using=None, keep_parents=False):
        self._remove_image()
        self.remove_image_vm()
        super().delete(using=using, keep_parents=keep_parents)

    def _remove_image(self):
        """
        删除image， 重命名镜像（不区分基础镜像与用户镜像）, 已删除镜像名格式为：x_image_{time}_{image_name}
        :return:
            True    # success
            raise Exception   # failed
        :raises: raise Exception
        """
        ceph_pool = self.ceph_pool
        if not ceph_pool:
            raise Exception('remove_image failed, can not get ceph_pool')
        pool_name = ceph_pool.pool_name
        config = ceph_pool.ceph
        if not config:
            raise Exception('remove_image failed, can not get ceph')

        try:
            rbd = get_rbd_manager(ceph=config, pool_name=pool_name)
            if rbd.image_exists(self.base_image):
                time_str = timezone.now().strftime('%Y%m%d%H%M%S')
                new_image_name = f"x_image_{time_str}_{self.base_image}"
                rbd.rename_image(image_name=self.base_image, new_name=new_image_name)
        except (RadosError, Exception) as e:
            raise Exception(f'remove snap or image error, {str(e)}')

        return True

    def remove_image_vm(self):
        try:
            if self.vm_uuid:
                from vms.api import VmAPI
                from vms.models import Vm
                vm = Vm(uuid=self.vm_uuid, name=self.vm_uuid, vcpu=self.vm_vcpu, mem=self.vm_mem, host=self.vm_host)
                api = VmAPI()
                api.delete_vm_for_image(vm)
        except Exception as e:
            raise Exception(f'remove vm of image error, {str(e)}')
        return True

    def get_size(self):
        if self.size == 0:
            self.update_size_from_ceph()

        return self.size

    def get_rbd_manager(self):
        """
        :raises: raise Exception
        """
        ceph_pool = self.ceph_pool
        if not ceph_pool:
            raise Exception('can not get ceph_pool')
        pool_name = ceph_pool.pool_name
        config = ceph_pool.ceph
        if not config:
            raise Exception('can not get ceph config')

        return get_rbd_manager(ceph=config, pool_name=pool_name)

    def get_size_from_ceph(self, image_name: str):
        """
        :return:
            int     # in bytes
        """
        try:
            rbd = self.get_rbd_manager()
            return rbd.get_rbd_image_size(image_name)
        except (RadosError, Exception) as e:
            raise Exception(str(e))

    def update_size_from_ceph(self):
        size = self.get_size_from_ceph(image_name=self.base_image)
        size_gb = math.ceil(size / 1024 ** 3)
        self.size = size_gb
        self.save(update_fields=['size'])

    def get_center(self):
        """获取数据中心"""
        return self.ceph_pool.ceph.center


class MirrorImageTask(models.Model):
    """公共镜像任务表"""

    OPERATE_PULL = 1
    OPERATE_PUSH = 2
    OPERATE_CHOICES = (
        (OPERATE_PULL, '下载'),
        (OPERATE_PUSH, '上传'),
    )

    DOWNLOADING = 1
    DOWNLOADCOMPLATE = 2
    UPLOADING = 3
    UPLOADCOMPLATE = 4
    UPLOADFAILURE = 5
    DOWNLOADFAILURE = 6
    NONESTATUS = 7
    TASK_STATUS_CHOICES = (
        (DOWNLOADING, '下载中'),
        (DOWNLOADCOMPLATE, '下载完成'),
        (UPLOADING, '上传中'),
        (UPLOADCOMPLATE, '上传完成'),
        (UPLOADFAILURE, '上传失败'),
        (DOWNLOADFAILURE, '下载失败'),
        (NONESTATUS, '无'),
    )

    mirror_image_name = models.CharField(verbose_name=_('镜像名称'), max_length=100)
    mirror_image_sys_type = models.CharField(verbose_name=_('系统类型'), max_length=100, default='Linux',
                                             help_text='Windows、Linux、Unix、MacOS、Android、其他')
    mirror_image_version = models.CharField(verbose_name=_('系统发行编号'), max_length=100, default='stream 9')
    mirror_image_release = models.CharField(verbose_name=_('系统发行版本'), max_length=100, default='Centos',
                                            help_text='Centos、Ubuntu、Windows Desktop、Windows Server、Fedora、Rocky、Unknown')
    mirror_image_architecture = models.CharField(verbose_name=_('系统架构'), max_length=100, default='x86-64',
                                                 help_text='x86-64、i386、arm-64、unknown')
    mirror_image_boot_mode = models.CharField(verbose_name=_('系统启动方式'), max_length=100, default='BIOS',
                                              help_text='BIOS、UEFI')
    mirror_image_base_image = models.CharField(verbose_name=_('镜像'), max_length=200, default='',
                                               help_text='导入ceph的镜像需要的名称')
    mirror_image_enable = models.BooleanField(verbose_name=_('启用'), default=True,
                                              help_text="镜像导入成功后，会启用镜像，否则不会启用")

    mirror_image_xml_tpl = models.IntegerField(verbose_name=_('xml模板'), help_text='找到xml模板的数据,填写id')
    user = models.CharField(verbose_name=_('用户'), max_length=255, default='', null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    desc = models.TextField(verbose_name=_('描述'), blank=True, null=True, default=None)
    mirror_image_default_user = models.CharField(verbose_name=_('系统默认登录用户名'), max_length=32, default='root')
    mirror_image_default_password = models.CharField(verbose_name=_('系统默认登录密码'), max_length=32,
                                                     default='cnic.cn')
    mirror_image_size = models.IntegerField(verbose_name=_('镜像大小（Gb）'), default=0,
                                            help_text='image size不是整Gb大小，要向上取整，如1.1GB向上取整为2Gb')

    operate = models.SmallIntegerField(verbose_name=_('操作'), choices=OPERATE_CHOICES, default=OPERATE_PULL)
    update_local_path = models.CharField(verbose_name=_('上传本地存储路径'), max_length=100, default='/00_data/mirror_image/upload/')
    download_local_path = models.CharField(verbose_name=_('下载本地存储路径'), max_length=100, default='/00_data/mirror_image/downnlod/')
    mirrors_image_service_url = models.CharField(verbose_name=_('公共镜像地址'), max_length=255)
    status = models.SmallIntegerField(verbose_name=_('任务状态'), choices=TASK_STATUS_CHOICES, default=DOWNLOADING)
    import_date = models.DateTimeField(verbose_name=_('导入开始时间'), null=True, blank=True, default=None)
    import_date_complate = models.DateTimeField(verbose_name=_('导入完成时间'), null=True, blank=True, default=None)
    export_date = models.DateTimeField(verbose_name=_('导出开始时间'), null=True, blank=True, default=None)
    export_date_complate = models.DateTimeField(verbose_name=_('导出完成时间'), null=True, blank=True, default=None)
    error_msg = models.CharField(verbose_name=_('错误信息'), max_length=1000, null=True, blank=True, default=None)
    bucket_name = models.CharField(verbose_name=_('存储桶名称'), max_length=255, default='')
    file_path = models.CharField(verbose_name=_('文件路径'), max_length=500, default='')
    token = models.CharField(verbose_name=_('存储桶token'), max_length=500, default='')
    # image_import_or_export_name = models.CharField(verbose_name=_('导入或导出的镜像名称'), max_length=255, default=None,
    #                                                blank=True, null=True)
    local_hostname = models.CharField(verbose_name=_('本地hosnname'), max_length=255, default=None, blank=True,
                                      null=True)
    download_or_upload_status = models.BooleanField(verbose_name=_('下载或上传完成'), default=False)
    create_os_image = models.BooleanField(verbose_name=_('创建操作系统镜像完成'), default=False)

    class Meta:
        ordering = ['-id']
        db_table = 'app_image_mirror_image_task'
        verbose_name = _('公共镜像任务表')
        verbose_name_plural = _('公共镜像任务表')
        unique_together = ('mirror_image_name', 'mirror_image_version', 'operate')

    def __str__(self):
        return self.mirror_image_name
