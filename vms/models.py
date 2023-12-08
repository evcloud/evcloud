import math

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

from image.models import Image
from compute.models import Host, Center
from network.models import MacIP
from ceph.managers import get_rbd_manager, CephClusterManager, RadosError
from ceph.models import CephPool
from compute.managers import HostManager
from utils.ev_libvirt.virt import VmDomain
from utils.errors import Error

# 获取用户模型
User = get_user_model()


def remove_image(ceph, pool_name: str, image_name: str):
    """
    删除一个镜像

    :return:
        True            # success
        raise Error()   # failed

    :raises: Error
    """
    try:
        rbd = get_rbd_manager(ceph=ceph, pool_name=pool_name)
        rbd.remove_image(image_name=image_name)
    except (RadosError, Exception) as e:
        raise Error(msg=str(e))

    return True


def rename_image(ceph, pool_name: str, image_name: str, new_name: str):
    """
    重命名一个镜像

    :return:
        True    # success
        raise Error()   # failed

    :raises: Error
    """
    try:
        rbd = get_rbd_manager(ceph=ceph, pool_name=pool_name)
        rbd.rename_image(image_name=image_name, new_name=new_name)
    except (RadosError, Exception) as e:
        raise Error(msg=str(e))

    return True


class VmBase(models.Model):
    class DiskType(models.TextChoices):
        CEPH_RBD = 'ceph-rbd', 'Ceph rbd'
        LOCAL = 'local', '本地硬盘'

    disk_type = models.CharField(verbose_name='系统盘类型', max_length=16,
                                 choices=DiskType.choices, default=DiskType.CEPH_RBD)
    sys_disk_size = models.IntegerField(verbose_name='系统盘大小(Gb)', default=0, help_text='系统盘大小不能小于image大小')

    class Meta:
        abstract = True

    def is_sys_disk_local(self):
        return self.disk_type == self.DiskType.LOCAL


class Vm(VmBase):
    """
    虚拟机模型
    """
    class VmStatus(models.TextChoices):
        SHELVE = 'shelve', _('搁置')
        NORMAL = 'normal', _('正常')

    uuid = models.CharField(verbose_name='虚拟机UUID', max_length=36, primary_key=True)
    name = models.CharField(verbose_name='名称', max_length=200)
    vcpu = models.IntegerField(verbose_name='CPU数')
    mem = models.IntegerField(verbose_name='内存大小', help_text='单位GB')
    disk = models.CharField(verbose_name='系统盘名称', max_length=100, unique=True,
                            help_text='vm自己的系统盘，保存于ceph中的rdb文件名称')
    image = models.ForeignKey(
        to=Image, on_delete=models.SET_NULL, db_constraint=False, null=True, blank=True, default=None,
        verbose_name='源镜像', help_text='创建此虚拟机时使用的源系统镜像，disk从image复制')
    user = models.ForeignKey(to=User, verbose_name='创建者', on_delete=models.SET_NULL,
                             related_name='user_vms', null=True)
    create_time = models.DateTimeField(verbose_name='创建日期', auto_now_add=True)
    remarks = models.TextField(verbose_name='备注', default='', blank=True)
    init_password = models.CharField(max_length=20, default='', blank=True, verbose_name='root初始密码')

    host = models.ForeignKey(to=Host, on_delete=models.CASCADE, verbose_name='宿主机', blank=True, null=True, default=None)
    xml = models.TextField(verbose_name='虚拟机当前的XML', help_text='定义虚拟机的当前的XML内容')
    mac_ip = models.OneToOneField(to=MacIP, on_delete=models.CASCADE, related_name='ip_vm', verbose_name='MAC IP',
                                  blank=True, null=True, default=None)

    image_name = models.CharField(verbose_name='镜像名称', max_length=100, default='')
    image_parent = models.CharField(verbose_name='父镜像RBD名', max_length=255, default='', help_text='虚拟机系统盘镜像的父镜像')
    image_snap = models.CharField(verbose_name='镜像快照', max_length=200, default='', blank=True, editable=True)
    image_size = models.IntegerField(
        verbose_name='镜像大小（Gb）', default=0, help_text='image size不是整Gb大小，要向上取整，如1.1GB向上取整为2Gb')
    sys_type = models.SmallIntegerField(
        verbose_name='系统类型', choices=Image.CHOICES_SYS_TYPE, default=Image.SYS_TYPE_OTHER)
    version = models.CharField(verbose_name='系统发行编号', max_length=100, default='')
    release = models.SmallIntegerField(
        verbose_name='系统发行版本', choices=Image.RELEASE_CHOICES, default=Image.RELEASE_CENTOS)
    architecture = models.SmallIntegerField(
        verbose_name='系统架构', choices=Image.ARCHITECTURE_CHOICES, default=Image.ARCHITECTURE_X86_64)
    boot_mode = models.SmallIntegerField(verbose_name='系统启动方式', choices=Image.BOOT_CHOICES, default=Image.BOOT_BIOS)
    nvme_support = models.BooleanField(verbose_name='支持NVME设备', default=False)
    ceph_pool = models.ForeignKey(
        to=CephPool, on_delete=models.DO_NOTHING, verbose_name='CEPH存储后端',
        null=True, db_constraint=False, db_index=False, default=None)
    default_user = models.CharField(verbose_name='系统默认登录用户名', max_length=32, default='root')
    default_password = models.CharField(verbose_name='系统默认登录密码', max_length=32, default='cnic.cn')
    image_desc = models.TextField(verbose_name='系统镜像描述', default='', blank=True)
    image_xml_tpl = models.TextField(verbose_name='XML模板', default='')
    vm_status = models.CharField(verbose_name='实际运行状态', max_length=16, choices=VmStatus.choices,
                                 default=VmStatus.NORMAL.value)
    last_ip = models.ForeignKey(to=MacIP, verbose_name='虚拟机最后使用ip', blank=True, null=True, default=None,
                                db_constraint=False, db_index=False, on_delete=models.SET_NULL, help_text='该字段在使用搁置服务时使用')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-create_time']
        verbose_name = '虚拟机'
        verbose_name_plural = '虚拟机'

    def get_uuid(self):
        return self.uuid

    @property
    def hex_uuid(self):
        return self.get_uuid()

    @hex_uuid.setter
    def hex_uuid(self, uuid):
        self.uuid = uuid

    @property
    def ipv4(self):
        return self.mac_ip.ipv4

    @property
    def host_ipv4(self):
        return self.host.ipv4

    def rm_sys_disk(self):
        """
        删除系统盘
        :return:
            True    # success
            False   # failed
        """
        ceph_pool = self.ceph_pool
        if not ceph_pool:
            return False
        pool_name = ceph_pool.pool_name
        config = ceph_pool.ceph
        if not config:
            return False

        try:
            remove_image(ceph=config, pool_name=pool_name, image_name=self.disk)
        except Error as e:
            return False

        return True

    def user_has_perms(self, user):
        """
        用户是否有访问此宿主机的权限
        :param user: 用户
        :return:
            True    # has
            False   # no
        """
        if not isinstance(user.id, int):  # 未认证用户
            return False

        if user.is_superuser:
            return True

        if self.user_id == user.id:
            return True

        return False

    @property
    def vdisks(self):
        """
        获取挂载到虚拟机下的所有虚拟硬盘查询集

        :return:
            QuerySet()
        """
        return self.vdisk_set.all()

    @property
    def sys_snaps(self):
        return self.sys_disk_snaps.all()

    def get_mounted_vdisk_queryset(self):
        """
        获取挂载到虚拟机下的所有虚拟硬盘查询集

        :return:
            QuerySet()
        """
        return self.vdisks

    def get_vm_mounted_vdisk_count(self):
        """
        获取虚拟机下已挂载虚拟硬盘的数量

        :return:
            int
        """
        qs = self.get_mounted_vdisk_queryset()
        return qs.count()

    @property
    def pci_devices(self):
        """
        获取挂载到虚拟机下的所有PCI设备查询集

        :return:
            QuerySet()
        """
        return self.device_set.select_related('host__group').all()

    def get_sys_disk_size(self):
        if self.sys_disk_size == 0:
            try:
                self.update_sys_disk_size()
            except Exception as e:
                pass

        return self.sys_disk_size

    def get_rbd_manager(self):
        ceph_pool = self.ceph_pool
        if not ceph_pool:
            raise Exception('can not get ceph_pool')
        pool_name = ceph_pool.pool_name
        config = ceph_pool.ceph
        if not config:
            raise Exception('can not get ceph config')

        return get_rbd_manager(ceph=config, pool_name=pool_name)

    def update_sys_disk_size(self):
        if self.disk_type == self.DiskType.CEPH_RBD:
            try:
                rbd_mgr = self.get_rbd_manager()
                size = rbd_mgr.get_rbd_image_size(self.disk)
            except (RadosError, Exception) as e:
                raise Exception(str(e))

            size_gb = math.ceil(size / 1024 ** 3)
            self.sys_disk_size = size_gb
            self.save(update_fields=['sys_disk_size'])

    def delete(self, using=None, keep_parents=False):
        """
        删除虚拟机时强制更新Host资源分配信息
        """
        super().delete(using=using, keep_parents=keep_parents)

    def save(self, *args, **kwargs):
        """
        新增虚拟机时强制更新Host资源分配信息
        """
        is_insert = False
        if not self.pk:
            is_insert = True
        super().save(*args, **kwargs)
        if is_insert:
            HostManager.update_host_quota(host_id=self.host_id)

    def update_image_fields(self, image: Image):
        """
        更新镜像有关的字段信息，只更新此对象实例 不保存到数据库

        :return: 更新字段名称的列表
        """
        self.image = image
        self.image_name = image.name
        self.image_parent = image.base_image
        self.image_snap = image.snap
        self.image_size = image.size
        self.sys_type = image.sys_type
        self.version = image.version
        self.release = image.release
        self.architecture = image.architecture
        self.boot_mode = image.boot_mode
        self.nvme_support = image.nvme_support
        self.ceph_pool_id = image.ceph_pool_id
        self.default_user = image.default_user
        self.default_password = image.default_password
        self.image_desc = image.desc
        self.image_xml_tpl = image.xml_tpl.xml
        return [
            'image', 'image_name', 'image_parent', 'image_snap', 'image_size', 'sys_type', 'version', 'release',
            'architecture', 'boot_mode', 'nvme_support', 'ceph_pool_id', 'default_user', 'default_password',
            'image_desc', 'image_xml_tpl'
        ]

    def get_attach_ip_list(self):
        att_list = []
        att = self.get_attach_ip()
        for ip in att:
            att_list.append(ip.sub_ip.ipv4)
        return att_list

    def get_attach_ip(self):
        return self.vm_attach.all()



class VmArchive(VmBase):
    """
    删除虚拟机归档记录
    """
    id = models.AutoField(verbose_name='ID', primary_key=True)
    uuid = models.CharField(verbose_name='虚拟机UUID', max_length=50, unique=True, blank=True, default='')
    name = models.CharField(verbose_name='名称', max_length=200)
    vcpu = models.IntegerField(verbose_name='CPU数')
    mem = models.IntegerField(verbose_name='内存大小')

    vlan_id = models.IntegerField(verbose_name='VLAN ID')
    br = models.CharField(verbose_name='网桥名', max_length=50, blank=True, default='')
    mac = models.CharField(verbose_name='MAC地址', max_length=50, blank=True, default='')
    ipv4 = models.CharField(verbose_name='IP地址', max_length=50, blank=True, default='')

    disk = models.CharField(verbose_name='系统盘名称', max_length=100, help_text='vm自己的系统盘，保存于ceph中的rdb文件名称')
    image_id = models.IntegerField(verbose_name='系统镜像id')
    image_parent = models.CharField(verbose_name='父镜像', max_length=255, help_text='虚拟机系统盘镜像的父镜像')
    xml = models.TextField(verbose_name='虚拟机当前的XML', help_text='定义虚拟机的当前的XML内容')
    ceph_id = models.IntegerField(verbose_name='CEPH集群id')
    ceph_pool = models.CharField(verbose_name='CEPH POOL', max_length=100, blank=True, default='')

    center_id = models.IntegerField(verbose_name='数据中心ID', blank=True, default=0)
    center_name = models.CharField(verbose_name='数据中心', max_length=100, blank=True, default='')
    group_id = models.IntegerField(verbose_name='宿主机组ID', blank=True, default=0)
    group_name = models.CharField(verbose_name='宿主机组', max_length=100, null=True, blank=True)
    host_id = models.IntegerField(verbose_name='宿主机ID', blank=True, default=0)
    host_ipv4 = models.CharField(verbose_name='宿主机IP', max_length=50, blank=True, default='')

    user = models.CharField(verbose_name='创建者', max_length=200, blank=True, default='')
    create_time = models.DateTimeField(verbose_name='VM创建日期')
    archive_time = models.DateTimeField(verbose_name='VM归档日期', auto_now_add=True)
    remarks = models.TextField(verbose_name='备注', default='', blank=True)
    host_released = models.BooleanField(verbose_name='宿主机资源是否释放', default=True, help_text='标记宿主机上的vm是否删除清理')

    class Meta:
        ordering = ['id']
        verbose_name = '虚拟机归档记录'
        verbose_name_plural = '虚拟机归档表'

    def delete(self, using=None, keep_parents=False):
        self.check_and_release_host()
        self.rm_sys_disk_snap()
        if not self.rm_sys_disk():
            raise Exception('remove rbd image of disk error')
        super().delete(using=using, keep_parents=keep_parents)

    def get_ceph_cluster(self):
        """
        获取ceph集群配置对象

        :return:
            CephCluster()   # success
            None            # error or not exists
        """
        try:
            ceph = CephClusterManager().get_ceph_by_id(self.ceph_id)
        except RadosError as e:
            return None

        if not ceph:
            return None

        return ceph

    def rm_sys_disk_snap(self):
        """
        删除系统盘快照

        :return:None
        :raises: Exception
        """
        if not self.disk:
            return

        snaps = VmDiskSnap.objects.select_related('ceph_pool', 'ceph_pool__ceph').filter(disk=self.disk).all()
        for snap in snaps:
            snap.delete()

    def rm_sys_disk(self, raise_exception=False):
        """
        删除系统盘，需要先删除所有系统盘快照

        :param raise_exception: 删除错误时是否抛出错误
        :return:
            True    # success
            False   # failed

        :raises: Error    # When raise_exception == True
        """
        if not self.disk:
            return True

        config = self.get_ceph_cluster()
        if not config:
            return False

        try:
            remove_image(ceph=config, pool_name=self.ceph_pool, image_name=self.disk)
        except Error as e:
            if raise_exception:
                raise Error(msg=str(e))

            return False

        self.disk = ''
        try:
            self.save(update_fields=['disk'])
        except Exception as e:
            pass

        return True

    def rename_sys_disk_archive(self):
        """
        虚拟机归档后，系统盘RBD镜像修改了已删除归档的名称，格式：x_{time}_{disk_name}
        :return:
            True    # success
            False   # failed
        """
        old_name = self.disk
        pool_name = self.ceph_pool

        config = self.get_ceph_cluster()
        if not config:
            return False

        ok, new_name = rename_sys_disk_delete(ceph=config, pool_name=pool_name, disk_name=old_name)
        if not ok:
            return False

        self.disk = new_name
        try:
            self.save(update_fields=['disk'])
        except Exception as e:
            try:
                rename_image(ceph=config, pool_name=pool_name, image_name=new_name, new_name=old_name)
            except Exception as exc:
                pass
            return False

        return True

    def is_host_released(self):
        return self.host_released

    def set_host_released(self, released: bool = True):
        self.host_released = released
        try:
            self.save(update_fields=['host_released'])
        except Exception as e:
            return False

        return True

    def set_host_not_release(self):
        return self.set_host_released(False)

    def check_and_release_host(self):
        """
        检查并从宿主机删除vm
        :return:
            True

        :raises: Error
        """
        if not self.is_host_released():
            domain = VmDomain(host_ip=self.host_ipv4, vm_uuid=self.uuid)
            try:
                if not domain.undefine():
                    raise Exception('Failed to delete vm form host.')
            except Exception as e:
                raise Error(msg=str(e))

        self.set_host_released()
        return True


class VmLog(models.Model):
    """
    虚拟机相关的记录
    """
    ABOUT_NORMAL = 0
    ABOUT_MAC_IP = 1
    ABOUT_MEM_CPU = 2
    ABOUT_DISK = 3
    ABOUT_VM_METADATA = 4
    ABOUT_VM_ARCHIVE = 5
    ABOUT_HOST_VM_CREATED = 6
    ABOUT_VM_DISK = 7
    ABOUT_VM_GPU = 8

    ABOUT_VALUE_TUPLE = tuple(range(0, 9))

    ABOUT_CHOICES = (
        (ABOUT_NORMAL, '普通'),
        (ABOUT_MAC_IP, '有关MAC IP资源'),
        (ABOUT_MEM_CPU, '有关MEM CPU资源'),
        (ABOUT_DISK, '有关系统盘资源'),
        (ABOUT_VM_METADATA, '有关虚拟机元数据'),
        (ABOUT_VM_ARCHIVE, '有关虚拟机归档记录'),
        (ABOUT_HOST_VM_CREATED, '有关宿主机已创建虚拟机数量'),
        (ABOUT_VM_DISK, '有关虚拟硬盘'),
        (ABOUT_VM_GPU, '有关GPU'),
    )

    id = models.AutoField(verbose_name='ID', primary_key=True)
    title = models.CharField(verbose_name='标题', max_length=100, default='')
    content = models.TextField(verbose_name='日志内容', default='')
    about = models.SmallIntegerField(verbose_name='关于日志', choices=ABOUT_CHOICES, default=ABOUT_NORMAL)
    create_time = models.DateTimeField(verbose_name='时间', auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = '虚拟机相关错误日志'
        verbose_name_plural = '虚拟机相关错误日志'

    def __str__(self):
        return f'{self.get_about_display()}<{self.title}>'

    def about_str(self):
        return self.get_about_display()

    @classmethod
    def to_valid_about_value(cls, value: int):
        """
        转换为有效的about可选值

        :param value: input value
        :return: int
        """
        if value in cls.ABOUT_VALUE_TUPLE:
            return value

        return cls.ABOUT_NORMAL


class VmDiskSnap(models.Model):
    """
    虚拟机系统盘快照
    """
    id = models.AutoField(verbose_name='ID', primary_key=True)
    vm = models.ForeignKey(to=Vm, on_delete=models.SET_NULL, related_name='sys_disk_snaps',
                           null=True, verbose_name='虚拟机')
    ceph_pool = models.ForeignKey(to=CephPool, on_delete=models.SET_NULL, null=True, verbose_name='CEPH POOL')
    disk = models.CharField(max_length=100, verbose_name='虚拟机系统盘')  # 同虚拟机uuid
    snap = models.CharField(max_length=100, verbose_name='系统盘CEPH快照')  # 默认名称为 disk-snap创建日期
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建日期')
    remarks = models.TextField(default='', null=True, blank=True, verbose_name='备注')

    class Meta:
        ordering = ['-id']
        verbose_name = '虚拟机系统盘快照'
        verbose_name_plural = '虚拟机系统盘快照'

    def __str__(self):
        return self.snap

    @property
    def sys_disk(self):
        if self.disk:
            return self.disk

        if self.vm:
            return self.vm.disk

        raise Exception('can not get vm disk')

    def get_ceph_pool(self):
        """
        获取系统盘所在的ceph pool对象
        :return:
            CephPool()  # success
            None        # failed
        """
        if self.ceph_pool:
            return self.ceph_pool

        if self.vm:
            self.ceph_pool = self.vm.ceph_pool

        return self.ceph_pool

    def get_rbd_manager(self):
        """
        :raises: Exception
        """
        ceph_pool = self.get_ceph_pool()
        if not ceph_pool:
            raise Exception('can not get ceph pool')

        pool_name = ceph_pool.pool_name
        config = ceph_pool.ceph
        if not config:
            raise Exception('can not get ceph')

        return get_rbd_manager(ceph=config, pool_name=pool_name)

    def _create_sys_snap(self):
        """
        创建系统盘快照
        :return:
            True    # success

        :raises: Exception
        """
        now_timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        try:
            disk = self.sys_disk
            snap_name = f'{disk}-{now_timestamp}'
            rbd = self.get_rbd_manager()
            rbd.create_snap(image_name=disk, snap_name=snap_name)
        except (RadosError, Exception) as e:
            raise Exception(str(e))

        self.snap = snap_name
        return True

    def _remove_sys_snap(self):
        """
        删除系统盘快照
        :return:
            True    # success

        :raises: Exception
        """
        try:
            rbd = self.get_rbd_manager()
            rbd.remove_snap(image_name=self.sys_disk, snap=self.snap)
        except (RadosError, Exception) as e:
            raise Exception(str(e))

        return True

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.snap:
            self._create_sys_snap()
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def delete(self, using=None, keep_parents=False):
        if self.snap:
            self._remove_sys_snap()
        super().delete(using=using, keep_parents=keep_parents)


class MigrateTask(models.Model):
    class Tag(models.TextChoices):
        MIGRATE_LIVE = 'live', _('动态迁移')
        MIGRATE_STATIC = 'static', _('静态迁移')

    class Status(models.TextChoices):
        WAITING = 'wait', _('等待迁移')
        FAILED = 'failed', _('迁移失败')
        IN_PROCESS = 'in-process', _('正在迁移')
        SOME_TODO = 'some-todo', _('迁移完成，有些需要善后的工作')
        COMPLETE = 'complete', _('迁移完成')

    id = models.BigAutoField(primary_key=True)
    vm = models.ForeignKey(to=Vm, on_delete=models.SET_NULL, null=True, blank=True, default=None,
                           related_name='migrate_log_set')
    vm_uuid = models.CharField(max_length=36, verbose_name='虚拟机UUID')

    src_host = models.ForeignKey(to=Host, on_delete=models.SET_NULL, null=True, blank=True,
                                 default=None, related_name='src_migrate_log_set')
    src_host_ipv4 = models.GenericIPAddressField(verbose_name='源宿主机IP')
    src_undefined = models.BooleanField(default=False, verbose_name="是否已清理源虚拟机")
    src_is_free = models.BooleanField(default=False, verbose_name="是否释放源宿主机资源")

    dst_host = models.ForeignKey(to=Host, on_delete=models.SET_NULL, null=True, blank=True,
                                 default=None, related_name='dst_migrate_log_set')
    dst_host_ipv4 = models.GenericIPAddressField(verbose_name='目标宿主机IP')
    dst_is_claim = models.BooleanField(default=False, verbose_name="是否扣除目标宿主机资源")

    migrate_time = models.DateTimeField(auto_now_add=True, verbose_name='迁移时间')
    migrate_complete_time = models.DateTimeField(null=True, blank=True, default=None, verbose_name='迁移完成时间')
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.COMPLETE,
                              verbose_name='迁移状态')
    content = models.TextField(null=True, blank=True, default='', verbose_name='文字记录')
    tag = models.CharField(max_length=16, choices=Tag.choices, default=Tag.MIGRATE_STATIC,
                           verbose_name='迁移类型')

    class Meta:
        ordering = ['-id']
        verbose_name = '虚拟机迁移记录'
        verbose_name_plural = '虚拟机迁移记录表'

    def do_save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """
        :return:
            None        # success
            Exception   # failed
        """
        try:
            self.save(force_insert=force_insert, force_update=force_update,
                      using=using, update_fields=update_fields)
        except Exception as e:
            return e

        return None

    def set_dest_claim(self, to: bool = True):
        if self.dst_is_claim is to:
            return True

        self.dst_is_claim = to
        r = self.do_save(update_fields=['dst_is_claim'])
        if r is None:
            return False

        return True


def rename_sys_disk_delete(ceph, pool_name: str, disk_name: str):
    """
    虚拟机系统盘RBD镜像修改已删除归档的名称，格式：x_{time}_{disk_name}
    :return:
        True, new_disk_name    # success
        False,new_disk_name   # failed
    """
    if disk_name.startswith('x_'):
        return True, disk_name

    time_str = timezone.now().strftime('%Y%m%d%H%M%S')
    new_name = f"x_{time_str}_{disk_name}"
    try:
        rename_image(ceph=ceph, pool_name=pool_name, image_name=disk_name, new_name=new_name)
    except Error as e:
        return False, disk_name

    return True, new_name


class Flavor(models.Model):
    """
    虚拟机硬件配置样式
    """
    id = models.AutoField(primary_key=True, verbose_name='ID')
    vcpus = models.IntegerField(verbose_name=_('虚拟CPU数'), validators=[MinValueValidator(1)])
    ram = models.IntegerField(verbose_name=_('内存'), validators=[MinValueValidator(1)], help_text=_('单位GB'))
    public = models.BooleanField(verbose_name=_('是否公开'), default=True, help_text=_('非公开的普通用户不可见，超级用户可见'))
    enable = models.BooleanField(verbose_name=_('是否可用'), default=True)

    class Meta:
        ordering = ['vcpus']
        verbose_name = _('虚拟机硬件配置样式')
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'VCPUS: {self.vcpus} / RAM{self.ram}'

    def __repr__(self):
        return f'Flavor<vcpus={self.vcpus}, ram={self.ram}>'


class AttachmentsIP(models.Model):
    """附加ip"""
    id = models.AutoField(primary_key=True, verbose_name='ID')
    vm = models.ForeignKey(to=Vm, verbose_name='虚拟机', on_delete=models.SET_NULL, null=True, blank=True, default=None,
                           db_constraint=False, db_index=False, related_name='vm_attach')
    sub_ip = models.OneToOneField(to=MacIP, verbose_name='附加MACIP', on_delete=models.SET_NULL, null=True, blank=True,
                                  default=None, db_constraint=False, db_index=False, related_name='attach_ip')

    class Meta:
        ordering = ['id']
        verbose_name = _('虚拟机附加ip')
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.vm.uuid