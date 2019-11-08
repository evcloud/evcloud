from django.db import models
from django.contrib.auth import get_user_model

from image.models import Image
from compute.models import Host
from network.models import MacIP
from ceph.managers import RbdManager, CephClusterManager, RadosError
from vdisk.manager import VdiskManager

#获取用户模型
User = get_user_model()


def remove_image(conf_file: str, keyring_file: str, pool_name: str, image_name: str):
    '''
    删除一个镜像

    :return:
        True    # success
        False   # failed
    '''
    try:
        rbd = RbdManager(conf_file=conf_file, keyring_file=keyring_file, pool_name=pool_name)
        rbd.remove_image(image_name=image_name)
    except RadosError as e:
        return False
    except Exception as e:
        return False

    return True


class Vm(models.Model):
    '''
    虚拟机模型
    '''
    uuid = models.UUIDField(verbose_name='虚拟机UUID', primary_key=True)
    name = models.CharField(verbose_name='名称', max_length=200)
    vcpu = models.IntegerField(verbose_name='CPU数')
    mem = models.IntegerField(verbose_name='内存大小')
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
        if isinstance(self.uuid, str):
            return self.uuid
        return self.uuid.hex

    @property
    def hex_uuid(self):
        return self.get_uuid()

    @hex_uuid.setter
    def hex_uuid(self, uuid):
        self.uuid = uuid

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

        config_file = config.get_config_file()
        keyring_file = config.get_keyring_file()

        return remove_image(conf_file=config_file, keyring_file=keyring_file, pool_name=pool_name, image_name=self.disk)

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

        if self.user == user:
            return True

        return False

    def get_mounted_vdisk_queryset(self):
        '''
        获取挂载到虚拟机下的所有虚拟硬盘查询集

        :return:
            QuerySet()
        '''
        vm_uuid = self.get_uuid()
        return VdiskManager().get_vm_vdisk_queryset(vm_uuid=vm_uuid)

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
        self.rm_sys_disk()
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

    def rm_sys_disk(self):
        '''
        删除系统盘
        :return:
            True    # success
            False   # failed
        '''
        config = self.get_ceph_cluster()
        if not config:
            return False

        pool_name = self.ceph_pool
        config_file = config.get_config_file()
        keyring_file = config.get_keyring_file()

        return remove_image(conf_file=config_file, keyring_file=keyring_file, pool_name=pool_name, image_name=self.disk)


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

