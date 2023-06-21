# coding=utf-8
from uuid import uuid4

from django.db import models
from django.db.models import F, Sum
from django.contrib.auth import get_user_model
from django.utils import timezone

from ceph.models import CephPool
from ceph.managers import get_rbd_manager, RadosError
from compute.models import Group
from vms.models import Vm
from utils import errors


User = get_user_model()


class Quota(models.Model):
    """
    计算集群在指定存储卷上可申请的存储容量限额，total集群总容量限额，vdisk对应单块云硬盘容量限额
    """
    id = models.AutoField(verbose_name='ID', primary_key=True)
    name = models.CharField(max_length=100, default='', verbose_name='存储池名称')
    group = models.ForeignKey(to=Group, verbose_name='宿主机组', null=True,
                              on_delete=models.CASCADE, related_name='quota_set')
    cephpool = models.ForeignKey(to=CephPool, verbose_name='CEPH存储池', null=True,
                                 on_delete=models.CASCADE, related_name='quota_set')
    total = models.IntegerField(verbose_name='可用总容量(GB)', default=0, help_text='单位GB')
    size_used = models.IntegerField(verbose_name='已使用容量(GB)', default=0, help_text='单位GB')
    max_vdisk = models.IntegerField(verbose_name='云硬盘最大容量(GB)', default=200, help_text='单位GB')
    enable = models.BooleanField(verbose_name='存储池是否可用', default=True, help_text='开启和暂停使用2中状态, '
                                                                                 '未开启使用不允许创建云硬盘时')

    class Meta:
        verbose_name = '云硬盘CEPH存储池'
        verbose_name_plural = '云硬盘CEPH存储池'
        unique_together = ('group', 'cephpool')

    def __str__(self):
        return self.name

    def get_all_disk_size(self):
        """
        实时从数据库统计此云硬盘CEPH存储池下的所有硬盘的总容量大小

        :return: int
            size: int   # success
            -1          # error
        """
        if not self.id:
            return -1
        try:
            a = Vdisk.objects.filter(quota=self.id).aggregate(total=Sum('size'))
        except Exception as e:
            return -1
        size = a.get('total', -1)
        return size if isinstance(size, int) else 0

    def meet_needs(self, size: int):
        """
        是否还有足够的容量

        :param size: 需要的容量大小GB
        :return:
            True    # 满足
            False   # 没有足够的容量
        """
        if self.total - self.size_used >= size:
            return True

        return False

    def check_disk_size_limit(self, size: int):
        """
        检查要创建的硬盘大小是否符合硬盘最大容量限制

        :param size: 硬盘大小
        :return:
            True    # 符合，未超过最大限制
            False   # 超过最大限制
        """
        if size > self.max_vdisk:
            return False

        return True

    def claim(self, size: int):
        """
        从云硬盘CEPH存储池申请资源

        :param size: 要申请的硬盘容量大小GB
        :return:
            True    # success
            False   # failed
        """
        if self.enable is False:  # 存储池未开启则不能申请资源
            return False

        if size <= 0:
            return True

        if not self.check_disk_size_limit(size=size):
            return False

        if not self.meet_needs(size):
            return False

        self.size_used = F('size_used') + size
        try:
            self.save(update_fields=['size_used'])
        except Exception as e:
            return False
        self.refresh_from_db()
        return True

    def free(self, size: int):
        """
        释放资源

        :param size: 要释放的容量大小GB
        :return:
            True    # success
            False   # failed
        """
        if size <= 0:
            return True

        self.size_used = F('size_used') - size
        try:
            self.save(update_fields=['size_used'])
        except Exception as e:
            return False
        self.refresh_from_db()
        return True

    def user_has_perm(self, user):
        """
        用户是否有使用权限
        :param user:
        :return:
            True    # has
            False   # no
        """
        if self.group:
            return self.group.user_has_perms(user)

        return False


class Vdisk(models.Model):
    """附加磁盘类"""
    uuid = models.CharField(max_length=64, primary_key=True, editable=False, blank=True, verbose_name='云硬盘UUID')
    size = models.IntegerField(verbose_name='容量大小GB', help_text='单位GB')
    vm = models.ForeignKey(to=Vm, related_name='vdisk_set', on_delete=models.SET_NULL,
                           null=True, blank=True, verbose_name='挂载于虚拟机')
    user = models.ForeignKey(to=User, null=True, on_delete=models.CASCADE,
                             related_name='vdisk_set', verbose_name='创建者')
    quota = models.ForeignKey(to=Quota, on_delete=models.CASCADE, null=True,
                              related_name='vdisk_set', verbose_name='云硬盘CEPH存储池')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    attach_time = models.DateTimeField(null=True, blank=True, verbose_name='挂载时间')
    dev = models.CharField(max_length=100, blank=True, editable=False, default='', verbose_name='虚拟机中disk的设备名称',
                           help_text="对应系统中硬盘挂载逻辑设备名称（vda-vdz）")
    enable = models.BooleanField(default=True, verbose_name='是否可用')
    deleted = models.BooleanField(default=False, verbose_name='已删除')
    remarks = models.TextField(blank=True, default='', verbose_name='备注')
    rbd_name = models.CharField(verbose_name='Ceph rbd name', max_length=64, blank=True, default='')
    
    class Meta:
        ordering = ['-create_time']
        verbose_name = 'CEPH云硬盘'
        verbose_name_plural = 'CEPH云硬盘'
        unique_together = ['uuid', 'quota']

    def __str__(self):
        return f'ceph_disk_{str(self.rbd_image_name)}'

    @property
    def rbd_image_name(self):
        if not self.rbd_name and self.uuid:
            self.rbd_name = self.uuid
            try:
                self.save(update_fields=['rbd_name'])
            except Exception as e:
                pass

        return self.rbd_name

    @rbd_image_name.setter
    def rbd_image_name(self, val):
        self.rbd_name = val

    @staticmethod
    def new_uuid_str():
        """
        生成一个新的uuid字符串
        :return: uuid:str
        """
        return uuid4().hex

    def get_bytes_size(self):
        """GB to Bytes size"""
        return self.size * 1024**3

    def get_GB_size(self):
        return self.size

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        # uuid有效认为已存在，只是更新信息
        if not self.uuid:
            # 新的记录，要创建新的ceph rbd image,
            self.uuid = self.new_uuid_str()
            self.rbd_image_name = self.uuid
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def create_ceph_disk(self):
        """
        创建硬盘对应的ceph rbd image

        :return:
            True    # success

        :raises: Exception
        """
        try:
            ceph_pool = self.quota.cephpool
            if not ceph_pool:
                raise Exception(f'硬盘存储池<{self.quota}>没有ceph pool信息')

            if not ceph_pool.enable:
                raise Exception(f'硬盘存储池<{self.quota}>的pool<{ceph_pool}>未开启使用')

            pool_name = ceph_pool.pool_name
            data_pool = ceph_pool.data_pool if ceph_pool.has_data_pool else None

            config = ceph_pool.ceph
            if not config:
                raise Exception(f'pool<{ceph_pool}>没有ceph集群配置信息')
        except Exception as e:
            raise e

        size = self.get_bytes_size()
        try:
            rbd = get_rbd_manager(ceph=config, pool_name=pool_name)
            rbd.create_image(name=self.rbd_image_name, size=size, data_pool=data_pool)
        except (RadosError, Exception) as e:
            raise e

        return True

    def do_delete(self, using=None, keep_parents=False):
        try:
            self.remove_ceph_disk()
        except Exception as e:
            raise Exception(f'remove ceph rbd image failed, {str(e)}')

        self.quota.free(size=self.size)  # 释放硬盘存储池资源
        super().delete(using=using, keep_parents=keep_parents)

    def remove_ceph_disk(self):
        """
        删除硬盘对应的ceph rbd image

        :return:
            None

        :raises: Exception
        """
        ceph_pool = self.quota.cephpool
        if not ceph_pool:
            return
        pool_name = ceph_pool.pool_name
        config = ceph_pool.ceph
        if not config:
            return

        try:
            rbd = get_rbd_manager(ceph=config, pool_name=pool_name)
            rbd.remove_image(image_name=self.rbd_image_name)
        except (RadosError, Exception) as e:
            raise e

    def user_has_perms(self, user):
        """
        用户是否有访问此硬盘的权限
        :param user: 用户
        :return:
            True    # has
            False   # no
        """
        if user.is_superuser:   # 超级用户
            return True

        if self.user == user:
            return True

        return False

    @staticmethod
    def xml_tpl(has_auth: bool = True):
        """disk xml template"""
        if has_auth:
            return """
            <disk type='network' device='disk'>
                  <driver name='qemu' cache='unsafe' discard='ignore'/>
                  <auth username='{auth_user}'>
                    <secret type='ceph' uuid='{auth_uuid}'/>
                  </auth>
                  <source protocol='rbd' name='{pool}/{name}'>
                    {hosts_xml}
                  </source>
                    <target dev='{dev}' bus='{bus}'/>   
            </disk>
            """
        return """
            <disk type='network' device='disk'>
                  <driver name='qemu' cache='unsafe' discard='ignore'/>
                  <source protocol='rbd' name='{pool}/{name}'>
                    {hosts_xml}
                  </source>
                    <target dev='{dev}' bus='{bus}'/>   
            </disk>
            """

    def xml_desc(self, dev: str = '', bus='virtio'):
        """
        disk xml
        :param dev: 硬盘未挂载时，需要传入此参数；硬盘挂载后，self.dev会记录挂载后的硬盘逻辑名称
        :param bus: 指定硬盘的总线驱动，默认 'virtio'
        :return: str
        """
        if not dev:
            dev = self.dev

        cephpool = self.quota.cephpool
        ceph = cephpool.ceph
        if ceph.has_auth:
            xml = self.xml_tpl().format(auth_user=ceph.username, auth_uuid=ceph.uuid, pool=cephpool.pool_name,
                                        name=self.uuid, hosts_xml=ceph.hosts_xml, dev=dev, bus=bus)
        else:
            xml = self.xml_tpl(has_auth=False).format(pool=cephpool.pool_name,
                                                      name=self.uuid, hosts_xml=ceph.hosts_xml, dev=dev, bus=bus)

        return xml

    @property
    def is_mounted(self):
        """
        是否已被挂载
        :return:
            True    # 已挂载
            False   # 未挂载
        """
        if self.vm:
            return True

        return False

    def soft_delete(self):
        """
        软删除
        :return:
            True    # success
            False   # failed
        """
        try:
            self.deleted = True
            self.save(update_fields=['deleted'])
        except Exception as e:
            return False

        return True

    def rename_disk_rbd_name(self):
        """
        云硬盘删除后，硬盘RBD镜像修改为已删除归档的名称，格式：x_{time}_{disk_name}
        :return:
            None

        :raises: Error
        """
        ceph_pool = self.quota.cephpool
        if not ceph_pool:
            return
        pool_name = ceph_pool.pool_name
        config = ceph_pool.ceph
        if not config:
            return

        rbd_image_name = self.rbd_image_name
        if rbd_image_name.startswith('x_vd_'):
            return

        time_str = timezone.now().strftime('%Y%m%d%H%M%S')
        new_name = f"x_vd_{time_str}_{rbd_image_name}"
        try:
            rbd = get_rbd_manager(ceph=config, pool_name=pool_name)
            rbd.rename_image(image_name=self.rbd_image_name, new_name=new_name)
        except (RadosError, Exception) as e:
            raise errors.VdiskError.from_error(e)

        self.rbd_name = new_name
        try:
            self.save(update_fields=['rbd_name'])
        except Exception as e:
            try:
                rbd.rename_image(image_name=new_name, new_name=rbd_image_name)
            except Exception as exc:
                pass

            raise errors.VdiskError.from_error(e)
