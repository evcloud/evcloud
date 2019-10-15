from django.db import models
from django.contrib.auth import get_user_model

from image.models import Image
from compute.models import Host
from network.models import MacIP
from ceph.managers import RbdManager, RadosError

#获取用户模型
User = get_user_model()

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
        verbose_name = '虚拟机'
        verbose_name_plural = '虚拟机'

    def get_uuid(self):
        if isinstance(self.uuid, str):
            return self.uuid
        return self.uuid.hex

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

        try:
            rbd = RbdManager(conf_file=config_file, keyring_file=keyring_file, pool_name=pool_name)
            rbd.remove_image(image_name=self.disk)
        except RadosError as e:
            return False
        except Exception as e:
            return False

        return True

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
