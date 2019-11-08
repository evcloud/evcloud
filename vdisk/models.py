#coding=utf-8
from uuid import uuid4

from django.db import models, transaction
from django.db.models import F, Sum
from django.contrib.auth import get_user_model
from django.utils import timezone

from ceph.models import CephPool
from ceph.managers import RbdManager, RadosError
from compute.models import Group


User = get_user_model()


class Quota(models.Model):
    '''
    计算集群在指定存储卷上可申请的存储容量限额，total集群总容量限额，vdisk对应单块云硬盘容量限额
    '''
    id = models.AutoField(verbose_name='ID', primary_key=True)
    name = models.CharField(max_length=100, default='', verbose_name='存储池名称')
    group = models.ForeignKey(to=Group, verbose_name='宿主机组', null=True, on_delete=models.CASCADE, related_name='quota_set')
    cephpool = models.ForeignKey(to=CephPool, verbose_name='CEPH存储池', null=True, on_delete=models.CASCADE, related_name='quota_set')
    total = models.IntegerField(verbose_name='可用总容量(GB)', default=0, help_text='单位GB')
    size_used = models.IntegerField(verbose_name='已使用容量(GB)', default=0, help_text='单位GB')
    max_vdisk = models.IntegerField(verbose_name='云硬盘最大容量(GB)', default=200, help_text='单位GB')

    class Meta:
        verbose_name = '云硬盘CEPH存储池'
        verbose_name_plural = '云硬盘CEPH存储池'
        unique_together = ('group', 'cephpool')

    def __str__(self):
        return self.name

    def get_all_disk_size(self):
        '''
        实时从数据库统计此云硬盘CEPH存储池下的所有硬盘的总容量大小

        :return: int
            size: int   # success
            -1          # error
        '''
        if not self.id:
            return -1
        try:
            a = Vdisk.objects.filter(quota=self.id).aggregate(total=Sum('size'))
        except Exception as e:
            return -1
        return a.get('total', -1)

    def meet_needs(self,size:int):
        '''
        是否还有足够的容量

        :param size: 需要的容量大小GB
        :return:
            True    # 满足
            False   # 没有足够的容量
        '''
        if self.total - self.size_used >= size:
            return True

        return False

    def check_disk_size_limit(self, size:int):
        '''
        检查要创建的硬盘大小是否符合硬盘最大容量限制

        :param size: 硬盘大小
        :return:
            True    # 符合，未超过最大限制
            False   # 超过最大限制
        '''
        if size > self.max_vdisk:
            return False

        return True

    def claim(self, size: int):
        '''
        从云硬盘CEPH存储池申请资源

        :param size: 要申请的硬盘容量大小GB
        :return:
            True    # success
            False   # failed
        '''
        if size <= 0:
            return True

        if not self.check_disk_size_limit(size=size):
            return False

        if not self.meet_needs(size):
            return False

        self.size_used = F('size_used') + size
        try:
            self.save()
        except Exception as e:
            return False
        self.refresh_from_db()
        return True

    def free(self, size: int):
        '''
        释放资源

        :param size: 要释放的容量大小GB
        :return:
            True    # success
            False   # failed
        '''
        if size <= 0:
            return True

        self.size_used = F('size_used') - size
        try:
            self.save()
        except Exception as e:
            return False
        self.refresh_from_db()
        return True


class Vdisk(models.Model):
    '''附加磁盘类'''
    uuid = models.CharField(max_length=64, primary_key=True, editable=False, blank=True, verbose_name='云硬盘UUID')
    size = models.IntegerField(verbose_name='容量大小GB', help_text='单位GB')
    vm = models.CharField(max_length=200, null=True, blank=True, verbose_name='挂载于虚拟机')
    user = models.ForeignKey(to=User, null=True, on_delete=models.CASCADE, related_name='vdisk_set', verbose_name='创建者')
    quota = models.ForeignKey(to=Quota, on_delete=models.CASCADE, null=True, related_name='vdisk_set', verbose_name='云硬盘CEPH存储池')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    attach_time = models.DateTimeField(null=True, blank=True, verbose_name='挂载时间')
    dev = models.CharField(max_length=100, blank=True, editable=False, default='', verbose_name='虚拟机中disk的设备名称',
                           help_text="对应系统中硬盘挂载逻辑设备名称（vda-vdz）")
    enable = models.BooleanField(default=True, verbose_name='是否可用')
    remarks = models.TextField(blank=True, default='', verbose_name='备注')
    
    class Meta:
        verbose_name = 'CEPH云硬盘'
        verbose_name_plural = 'CEPH云硬盘'
        unique_together = ['uuid', 'quota']

    def __str__(self):
        return f'ceph_disk_{str(self.uuid)}'

    @classmethod
    def new_uuid_str(self):
        '''
        生成一个新的uuid字符串
        :return: uuid:str
        '''
        return uuid4().hex

    def get_bytes_size(self):
        '''GB to Bytes size'''
        return self.size * 1024**3

    def get_GB_size(self):
        return self.size

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        # uuid有效认为已存在，只是更新信息
        if self.uuid:
            super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
            return

        # 新的记录，要创建新的ceph rbd image,
        self.uuid = self.new_uuid_str()
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
        if not self._create_ceph_disk():
            self.delete()
            raise Exception('create ceph rbd image failed')

    def _create_ceph_disk(self):
        '''
        创建硬盘对应的ceph rbd image

        :return:
            True    # success
            False   # failed
        '''
        try:
            ceph_pool = self.quota.cephpool
            if not ceph_pool:
                return False
            pool_name = ceph_pool.pool_name
            config = ceph_pool.ceph
            if not config:
                return False
        except Exception:
            return False

        config_file = config.get_config_file()
        keyring_file = config.get_keyring_file()

        size = self.get_bytes_size()
        try:
            rbd = RbdManager(conf_file=config_file, keyring_file=keyring_file, pool_name=pool_name)
            rbd.create_image(name=self.uuid, size=size)
        except (RadosError, Exception) as e:
            return False

        return True

    def delete(self, using=None, keep_parents=False):
        if not self._remove_ceph_disk():
            raise Exception('remove ceph rbd image failed')
        super().delete(using=using, keep_parents=keep_parents)

    def _remove_ceph_disk(self):
        '''
        删除硬盘对应的ceph rbd image

        :return:
            True    # success
            False   # failed
        '''
        try:
            ceph_pool = self.quota.cephpool
            if not ceph_pool:
                return False
            pool_name = ceph_pool.pool_name
            config = ceph_pool.ceph
            if not config:
                return False
        except Exception:
            return False

        config_file = config.get_config_file()
        keyring_file = config.get_keyring_file()

        try:
            rbd = RbdManager(conf_file=config_file, keyring_file=keyring_file, pool_name=pool_name)
            rbd.remove_image(image_name=self.uuid)
        except (RadosError, Exception) as e:
            return False

        return True

    def user_has_perms(self, user):
        '''
        用户是否有访问此硬盘的权限
        :param user: 用户
        :return:
            True    # has
            False   # no
        '''
        if user.is_superuser:   # 超级用户
            return True

        if self.user == user:
            return True

        return False

    @property
    def xml_tpl(self):
        '''disk xml template'''
        return '''
            <disk type='network' device='disk'>
                  <driver name='qemu'/>
                  <auth username='{auth_user}'>
                    <secret type='ceph' uuid='{auth_uuid}'/>
                  </auth>
                  <source protocol='rbd' name='{pool}/{name}'>
                    {hosts_xml}
                  </source>
                    <target dev='{dev}' bus='virtio'/>   
            </disk>
            '''

    def xml_desc(self, dev:str=''):
        '''
        disk xml
        :param dev: 硬盘未挂载时，需要传入此参数；硬盘挂载后，self.dev会记录挂载后的硬盘逻辑名称
        :return: str
        '''
        if not dev:
            dev = self.dev

        cephpool = self.quota.cephpool
        ceph = cephpool.ceph
        xml = self.xml_tpl.format(auth_user=ceph.username, auth_uuid=ceph.uuid, pool=cephpool.pool_name,
                                  name=self.uuid, hosts_xml=ceph.hosts_xml, dev=dev)
        return xml

    def is_mounted(self):
        '''
        是否已被挂载
        :return:
            True    # 已挂载
            False   # 未挂载
        '''
        if self.vm:
            return True

        return False


