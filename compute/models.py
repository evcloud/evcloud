from django.db import models
from django.db.models import F
from django.contrib.auth import get_user_model

from network.models import Vlan

#获取用户模型
User = get_user_model()

# Create your models here.

class Center(models.Model):
    '''
    分中心模型
    一个分中心对应一个存储后端，存储虚拟机相关的数据，Ceph集群，虚拟机的虚拟硬盘和系统镜像使用ceph块存储
    '''
    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name='数据中心名称', max_length=100, unique=True)
    location = models.CharField(verbose_name='位置', max_length=100)
    desc = models.CharField(verbose_name='简介', max_length=200, default='', blank=True)

    class Meta:
        ordering = ('id',)
        verbose_name = '分中心'
        verbose_name_plural = '01_分中心'

    def __str__(self):
        return self.name


class Group(models.Model):
    '''
    宿主机组模型

    组用于权限隔离，某一个用户创建的虚拟机只能创建在指定的组的宿主机上，无权使用其他组的宿主机
    '''
    id = models.AutoField(primary_key=True)
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name='group_set', verbose_name='组所属的分中心')
    name = models.CharField(max_length=100, verbose_name='组名称')
    desc = models.CharField(max_length=200, default='', blank=True, verbose_name='描述')
    users = models.ManyToManyField(to=User, blank=True, related_name='group_set')     # 有权访问此组的用户

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('id',)
        verbose_name = '宿主机组'
        verbose_name_plural = '02_宿主机组'
        unique_together = ('center', 'name')

    def user_has_perms(self, user:User):
        '''
        用户是否有访问此宿主机组的权限
        :param user: 用户
        :return:
            True    # has
            False   # no
        '''
        if user.is_superuser:   # 超级用户
            return True

        u = self.users.filter(id=user.id).first()
        if u:
            return True

        return False


class Host(models.Model):
    '''
    宿主机模型

    宿主机是真实的物理主机，是虚拟机的载体，虚拟机使用宿主机的资源在宿主机上运行
    一台宿主机可能连接多个vlan子网
    '''
    id = models.AutoField(primary_key=True)
    group = models.ForeignKey(to=Group, on_delete=models.CASCADE, related_name='hosts_set', verbose_name='宿主机所属的组')
    vlans = models.ManyToManyField(to=Vlan, verbose_name='VLAN子网', related_name='vlan_hosts') # 局域子网
    ipv4 = models.GenericIPAddressField(unique=True, verbose_name='宿主机ip')
    real_cpu = models.IntegerField(default=20, verbose_name='真实物理CPU总数')
    vcpu_total = models.IntegerField(default=24, verbose_name='虚拟CPU总数')
    vcpu_allocated = models.IntegerField(default=0, verbose_name='已分配CPU总数')
    mem_total = models.IntegerField(default=32768, verbose_name='宿主机总内存大小')
    mem_allocated = models.IntegerField(default=0, verbose_name='宿主机已分配内存大小')
    mem_reserved = models.IntegerField(default=2038, verbose_name='宿主机要保留的内存空间大小')
    vm_limit = models.IntegerField(default=10, verbose_name='本机可创建虚拟机数量上限')
    vm_created = models.IntegerField(default=0, verbose_name='本机已创建虚拟机数量')
    enable = models.BooleanField(default=True, verbose_name='宿主机状态')
    desc = models.CharField(max_length=200, default='', blank=True, verbose_name='描述')

    ipmi_host = models.CharField(max_length=100, default='', blank=True)
    ipmi_user = models.CharField(max_length=100, default='', blank=True)
    ipmi_password = models.CharField(max_length=100, default='', blank=True)

    class Meta:
        verbose_name = '宿主机'
        verbose_name_plural = '06_宿主机'

    def __str__(self):
        return self.ipv4

    def exceed_vm_limit(self):
        '''
        检查是否达到或超过的可创建宿主机的数量上限
        :return:
            True: 已到上限，
            False: 未到上限
        '''
        return self.vm_created >= self.vm_limit

    def exceed_mem_limit(self, mem:int):
        '''
        检查宿主机是否还有足够的内存可供使用
        :param mem: 需要的内存大小
        :return:
            True: 没有足够的内存可用
            False: 内存足够使用
        '''
        free_mem = self.mem_total - self.mem_reserved - self.mem_allocated
        return  mem > free_mem

    def exceed_vcpu_limit(self, vcpu:int):
        '''
        检查宿主机是否还有足够的cpu可供使用
        :param vcpu: 需要的vcpu数量
        :return:
            True: 没有足够的vcpu可用
            False: vcpu足够使用
        '''
        free_cpu = self.vcpu_total - self.vcpu_allocated
        return  vcpu > free_cpu

    def meet_needs(self, vcpu:int, mem:int):
        '''
        检查宿主机是否满足资源需求
        :param vcpu: 需要的vcpu数量
        :param mem: 需要的内存大小
        :return:
            True: 满足
            False: 不满足
        '''
        # 可创建虚拟机数量限制
        if self.exceed_vm_limit():
            return False

        # cpu是否满足
        if self.exceed_vcpu_limit(vcpu=vcpu):
            return False

        # 内存是否满足
        if self.exceed_mem_limit(mem=mem):
            return False

        return  True

    def contains_vlan(self, vlan:Vlan):
        '''
        宿主机是否属于子网

        :param host: 宿主机对象
        :param vlan: 子网
        :return:
            True    # 属于
            False   # 不属于
        '''
        if vlan in self.vlans.all():
            return True

        return False

    def claim(self, vcpu: int, mem: int):
        '''
        从宿主机申请的资源

        :param vcpu: 要申请的cpu数
        :param mem: 要申请的内存大小
        :return:
            True    # success
            False   # failed
        '''
        # 申请资源
        if vcpu <= 0 and mem <= 0:
            return True
        if vcpu > 0:
            self.vcpu_allocated = F('vcpu_allocated') + vcpu
        if mem > 0:
            self.mem_allocated = F('mem_allocated') + mem
        try:
            self.save()
            self.refresh_from_db()
        except Exception as e:
            return False

        return True

    def free(self, vcpu: int, mem: int):
        '''
        释放从宿主机申请的资源

        :param vcpu: 要释放的cpu数
        :param mem: 要释放的内存大小
        :return:
            True    # success
            False   # failed
        '''
        # 释放资源
        if vcpu <= 0 and mem <= 0:
            return True
        if vcpu > 0:
            self.vcpu_allocated = F('vcpu_allocated') - vcpu
        if mem > 0:
            self.mem_allocated = F('mem_allocated') - mem
        try:
            self.save()
            self.refresh_from_db()
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
        if self.group.user_has_perms(user=user):
            return True

        return False

    def vm_created_num_add_1(self, commit=True):
        '''
        已创建虚拟机数量+1
        :param commit: True,立即提交更新到数据库；False,不提交
        :return:
            True
            False
        '''
        self.vm_created = F('vm_created') + 1
        if not commit:
            return True

        try:
            self.save(update_fields=['vm_created'])
            self.refresh_from_db()
        except Exception as e:
            return False

        return True

    def vm_created_num_sub_1(self, commit=True):
        '''
        已创建虚拟机数量-1
        :param commit: True,立即提交更新到数据库；False,不提交
        :return:
            True
            False
        '''
        self.vm_created = F('vm_created') - 1
        if not commit:
            return True

        try:
            self.save(update_fields=['vm_created'])
            self.refresh_from_db()
        except Exception as e:
            return False

        return True


