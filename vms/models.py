from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

from image.models import Image
from compute.models import Host
from network.models import MacIP
from ceph.managers import get_rbd_manager, CephClusterManager, RadosError
from ceph.models import CephPool


#获取用户模型
User = get_user_model()


def remove_image(ceph, pool_name: str, image_name: str):
    '''
    删除一个镜像

    :return:
        True    # success
        False   # failed
    '''
    try:
        rbd = get_rbd_manager(ceph=ceph, pool_name=pool_name)
        rbd.remove_image(image_name=image_name)
    except (RadosError, Exception) as e:
        return False

    return True

def rename_image(ceph, pool_name: str, image_name: str, new_name: str):
    '''
    重命名一个镜像

    :return:
        True    # success
        False   # failed
    '''
    try:
        rbd = get_rbd_manager(ceph=ceph, pool_name=pool_name)
        rbd.rename_image(image_name=image_name, new_name=new_name)
    except (RadosError, Exception) as e:
        return False

    return True


class Vm(models.Model):
    '''
    虚拟机模型
    '''
    uuid = models.CharField(verbose_name='虚拟机UUID', max_length=36, primary_key=True)
    name = models.CharField(verbose_name='名称', max_length=200)
    vcpu = models.IntegerField(verbose_name='CPU数')
    mem = models.IntegerField(verbose_name='内存大小', help_text='单位MB')
    disk = models.CharField(verbose_name='系统盘名称', max_length=100, unique=True, help_text='vm自己的系统盘，保存于ceph中的rdb文件名称')
    image = models.ForeignKey(to=Image, on_delete=models.CASCADE, verbose_name='源镜像', help_text='创建此虚拟机时使用的源系统镜像，disk从image复制')
    user = models.ForeignKey(to=User, verbose_name='创建者', on_delete=models.SET_NULL, related_name='user_vms',  null=True)
    create_time = models.DateTimeField(verbose_name='创建日期', auto_now_add=True)
    remarks = models.TextField(verbose_name='备注', default='', blank=True)

    host = models.ForeignKey(to=Host, on_delete=models.CASCADE, verbose_name='宿主机')
    xml = models.TextField(verbose_name='虚拟机当前的XML', help_text='定义虚拟机的当前的XML内容')
    mac_ip = models.OneToOneField(to=MacIP, on_delete=models.CASCADE, related_name='ip_vm', verbose_name='MAC IP')

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
        '''
        删除系统盘
        :return:
            True    # success
            False   # failed
        '''
        ceph_pool = self.image.ceph_pool
        if not ceph_pool:
            return False
        pool_name = ceph_pool.pool_name
        config = ceph_pool.ceph
        if not config:
            return False

        return remove_image(ceph=config, pool_name=pool_name, image_name=self.disk)

    def user_has_perms(self, user):
        '''
        用户是否有访问此宿主机的权限
        :param user: 用户
        :return:
            True    # has
            False   # no
        '''
        if not isinstance(user.id, int): # 未认证用户
            return False

        if user.is_superuser:
            return True

        if self.user_id == user.id:
            return True

        return False

    @property
    def vdisks(self):
        '''
        获取挂载到虚拟机下的所有虚拟硬盘查询集

        :return:
            QuerySet()
        '''
        return self.vdisk_set.all()

    @property
    def sys_snaps(self):
        return self.sys_disk_snaps.all()

    def get_mounted_vdisk_queryset(self):
        '''
        获取挂载到虚拟机下的所有虚拟硬盘查询集

        :return:
            QuerySet()
        '''
        return self.vdisks

    def get_vm_mounted_vdisk_count(self):
        '''
        获取虚拟机下已挂载虚拟硬盘的数量

        :return:
            int
        '''
        qs = self.get_mounted_vdisk_queryset()
        return qs.count()


class VmArchive(models.Model):
    '''
    删除虚拟机归档记录
    '''
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

    center_id   = models.IntegerField(verbose_name='分中心ID', blank=True, default=0)
    center_name = models.CharField(verbose_name='分中心', max_length=100, blank=True, default='')
    group_id    = models.IntegerField(verbose_name='宿主机组ID', blank=True, default=0)
    group_name  = models.CharField(verbose_name='宿主机组', max_length=100, null=True, blank=True)
    host_id     = models.IntegerField(verbose_name='宿主机ID', blank=True, default=0)
    host_ipv4   = models.CharField(verbose_name='宿主机IP', max_length=50, blank=True, default='')

    user = models.CharField(verbose_name='创建者', max_length=200, blank=True, default='')
    create_time = models.DateTimeField(verbose_name='VM创建日期')
    archive_time = models.DateTimeField(verbose_name='VM归档日期', auto_now_add=True)
    remarks = models.TextField(verbose_name='备注', default='', blank=True)

    class Meta:
        ordering = ['id']
        verbose_name = '虚拟机归档记录'
        verbose_name_plural = '虚拟机归档表'

    def delete(self, using=None, keep_parents=False):
        self.rm_sys_disk_snap()
        if not self.rm_sys_disk():
            raise Exception('remove rbd image of disk error')
        super().delete(using=using, keep_parents=keep_parents)

    def get_ceph_cluster(self):
        '''
        获取ceph集群配置对象

        :return:
            CephCluster()   # success
            None            # error or not exists
        '''
        try:
            ceph = CephClusterManager().get_ceph_by_id(self.ceph_id)
        except RadosError as e:
            return None

        if not ceph:
            return None

        return ceph

    def rm_sys_disk_snap(self):
        '''
        删除系统盘快照

        :return:None
        :raises: Exception
        '''
        snaps = VmDiskSnap.objects.select_related('ceph_pool', 'ceph_pool__ceph').filter(disk=self.disk).all()
        for snap in snaps:
            snap.delete()

    def rm_sys_disk(self):
        '''
        删除系统盘，需要先删除所有系统盘快照
        :return:
            True    # success
            False   # failed
        '''
        config = self.get_ceph_cluster()
        if not config:
            return False

        return remove_image(ceph=config, pool_name=self.ceph_pool, image_name=self.disk)

    def rename_sys_disk_archive(self):
        '''
        虚拟机归档后，系统盘RBD镜像修改了已删除归档的名称，格式：x_{time}_{disk_name}
        :return:
            True    # success
            False   # failed
        '''
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
            rename_image(ceph=config, pool_name=pool_name, image_name=new_name, new_name=old_name)
            return False

        return True


class VmLog(models.Model):
    '''
    虚拟机相关的记录
    '''
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
    def to_valid_about_value(self, value:int):
        '''
        转换为有效的about可选值

        :param value: input value
        :return: int
        '''
        if value in self.ABOUT_VALUE_TUPLE:
            return value

        return self.ABOUT_NORMAL


class VmDiskSnap(models.Model):
    '''
    虚拟机系统盘快照
    '''
    id = models.AutoField(verbose_name='ID', primary_key=True)
    vm = models.ForeignKey(to=Vm, on_delete=models.SET_NULL, related_name='sys_disk_snaps', null=True, verbose_name='虚拟机')
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
        '''
        获取系统盘所在的ceph pool对象
        :return:
            CephPool()  # success
            None        # failed
        '''
        if self.ceph_pool:
            return self.ceph_pool
        if self.vm and self.vm.image:
            self.ceph_pool = self.vm.image.ceph_pool
        return self.ceph_pool

    def _create_sys_snap(self):
        '''
        创建系统盘快照
        :return:
            True    # success

        :raises: Exception
        '''
        ceph_pool = self.get_ceph_pool()
        if not ceph_pool:
            raise Exception('can not get ceph pool')

        pool_name = ceph_pool.pool_name
        config = ceph_pool.ceph
        if not config:
            raise Exception('can not get ceph')

        now_timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        try:
            disk = self.sys_disk
            snap_name = f'{disk}-{now_timestamp}'
            rbd = get_rbd_manager(ceph=config, pool_name=pool_name)
            rbd.create_snap(image_name=disk, snap_name=snap_name)
        except (RadosError, Exception) as e:
            raise Exception(str(e))

        self.snap = snap_name
        return True

    def _remove_sys_snap(self):
        '''
        删除系统盘快照
        :return:
            True    # success

        :raises: Exception
        '''
        ceph_pool = self.get_ceph_pool()
        if not ceph_pool:
            raise Exception('can not get ceph pool')

        pool_name = ceph_pool.pool_name
        config = ceph_pool.ceph
        if not config:
            raise Exception('can not get ceph')

        try:
            rbd = get_rbd_manager(ceph=config, pool_name=pool_name)
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


class MigrateLog(models.Model):
    id = models.AutoField(primary_key=True)
    vm_uuid = models.CharField(max_length=36, verbose_name='虚拟机UUID')
    src_host_id = models.IntegerField(verbose_name='源宿主机ID')
    src_host_ipv4 = models.GenericIPAddressField(verbose_name='源宿主机IP')
    dst_host_id = models.IntegerField(verbose_name='目标宿主机ID')
    dst_host_ipv4 = models.GenericIPAddressField(verbose_name='目标宿主机IP')
    migrate_time = models.DateTimeField(auto_now_add=True, verbose_name='迁移时间')
    result = models.BooleanField(verbose_name='迁移结果(无错误)')
    content = models.TextField(null=True, blank=True, verbose_name='文字记录')
    src_undefined = models.BooleanField(default=False, verbose_name="已清理源云主机")

    class Meta:
        ordering = ['-id']
        verbose_name = '虚拟机迁移记录'
        verbose_name_plural = '虚拟机迁移记录表'

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
    ok = rename_image(ceph=ceph, pool_name=pool_name, image_name=disk_name, new_name=new_name)
    if not ok:
        return False, disk_name

    return True, new_name

