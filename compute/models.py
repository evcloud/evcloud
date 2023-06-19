from django.db import models
from django.db.models import F, Sum, Count
from django.contrib.auth import get_user_model

from pcservers.models import PcServer
from utils.errors import ComputeError

User = get_user_model()  # 获取用户模型


class Center(models.Model):
    """
    数中心中心模型
    一个数据中心对应一个存储后端，存储虚拟机相关的数据，Ceph集群，虚拟机的虚拟硬盘和系统镜像使用ceph块存储
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name='数据中心名称', max_length=100, unique=True)
    location = models.CharField(verbose_name='位置', max_length=100)
    desc = models.CharField(verbose_name='简介', max_length=200, default='', blank=True)

    class Meta:
        ordering = ('id',)
        verbose_name = '数据中心'
        verbose_name_plural = '01_数据中心'

    def __str__(self):
        return self.name


class Group(models.Model):
    """
    宿主机组模型

    组用于权限隔离，某一个用户创建的虚拟机只能创建在指定的组的宿主机上，无权使用其他组的宿主机
    """
    id = models.AutoField(primary_key=True)
    center = models.ForeignKey(Center, on_delete=models.CASCADE, related_name='group_set', verbose_name='组所属的数据中心')
    name = models.CharField(max_length=100, verbose_name='组名称')
    enable = models.BooleanField(default=True, verbose_name='启用宿主机组')
    desc = models.CharField(max_length=200, default='', blank=True, verbose_name='描述')
    users = models.ManyToManyField(to=User, blank=True, related_name='group_set')  # 有权访问此组的用户

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('id',)
        verbose_name = '宿主机组'
        verbose_name_plural = '02_宿主机组'
        unique_together = ('center', 'name')

    def user_has_perms(self, user: User):
        """
        用户是否有访问此宿主机组的权限
        :param user: 用户
        :return:
            True    # has
            False   # no
        """
        if not user or not user.id:
            return False

        if user.is_superuser:  # 超级用户
            return True

        return self.users.filter(id=user.id).exists()

    @property
    def vlans(self):
        """
        子网查询集
        :return:
        """
        return self.vlan_set.all()


class Host(models.Model):
    """
    宿主机模型

    宿主机是真实的物理主机，是虚拟机的载体，虚拟机使用宿主机的资源在宿主机上运行
    """
    id = models.AutoField(primary_key=True)
    group = models.ForeignKey(to=Group, on_delete=models.CASCADE, related_name='hosts_set', verbose_name='宿主机所属的组')
    pcserver = models.OneToOneField(to=PcServer, related_name='pc_server_host', blank=True, null=True,
                                    on_delete=models.CASCADE, verbose_name='物理服务器')
    ipv4 = models.GenericIPAddressField(unique=True, verbose_name='宿主机ip')
    real_cpu = models.IntegerField(default=20, verbose_name='真实物理CPU(核)')
    real_mem = models.IntegerField(default=30, verbose_name='真实物理内存(Gb)')
    vcpu_total = models.IntegerField(default=24, verbose_name='虚拟CPU(核）')
    vcpu_allocated = models.IntegerField(default=0, verbose_name='已用CPU（核）')
    mem_total = models.IntegerField(default=30, verbose_name='虚拟内存(GB)')
    mem_allocated = models.IntegerField(default=0, verbose_name='已用内存(GB)')
    vm_limit = models.IntegerField(default=10, verbose_name='本地云主机数量上限')
    vm_created = models.IntegerField(default=0, verbose_name='本地已创建云主机数量')
    enable = models.BooleanField(default=True, verbose_name='启用宿主机')
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
        """
        检查是否达到或超过的可创建宿主机的数量上限
        :return:
            True: 已到上限，
            False: 未到上限
        """
        return self.vm_created >= self.vm_limit

    def exceed_mem_limit(self, mem: int):
        """
        检查宿主机是否还有足够的内存可供使用
        :param mem: 需要的内存大小
        :return:
            True: 没有足够的内存可用
            False: 内存足够使用
        """
        free_mem = self.mem_total - self.mem_allocated
        return mem > free_mem

    def exceed_vcpu_limit(self, vcpu: int):
        """
        检查宿主机是否还有足够的cpu可供使用
        :param vcpu: 需要的vcpu数量
        :return:
            True: 没有足够的vcpu可用
            False: vcpu足够使用
        """
        free_cpu = self.vcpu_total - self.vcpu_allocated
        return vcpu > free_cpu

    def meet_needs(self, vcpu: int, mem: int, check_vm_limit: bool = True):
        """
        检查宿主机是否满足资源需求
        :param vcpu: 需要的vcpu数量
        :param mem: 需要的内存大小
        :param check_vm_limit: True(检查是否达到vm数量限制，是否还能创建vm)；False(不检查)
        :return:
            True: 满足
            False: 不满足
        """
        # 可创建虚拟机数量限制
        if check_vm_limit and self.exceed_vm_limit():
            return False

        # cpu是否满足
        if self.exceed_vcpu_limit(vcpu=vcpu):
            return False

        # 内存是否满足
        if self.exceed_mem_limit(mem=mem):
            return False

        return True

    def claim(self, vcpu: int, mem: int):
        """
        从宿主机申请的资源

        :param vcpu: 要申请的cpu数
        :param mem: 要申请的内存大小
        :return:
            True    # success
            False   # failed
        """
        # 申请资源
        if vcpu <= 0 and mem <= 0:
            return True

        cpu_delta = 0
        mem_delta = 0
        if vcpu > 0:
            cpu_delta = vcpu

        if mem > 0:
            mem_delta = mem

        return self.deduct_delta(cpu_delta=cpu_delta, mem_delta=mem_delta)

    def free(self, vcpu: int, mem: int):
        """
        释放从宿主机申请的资源

        :param vcpu: 要释放的cpu数
        :param mem: 要释放的内存大小
        :return:
            True    # success
            False   # failed
        """
        # 释放资源
        if vcpu <= 0 and mem <= 0:
            return True

        cpu_delta = 0
        mem_delta = 0
        if vcpu > 0:
            cpu_delta = -vcpu

        if mem > 0:
            mem_delta = -mem

        return self.deduct_delta(cpu_delta=cpu_delta, mem_delta=mem_delta)

    def deduct_delta(self, cpu_delta: int = 0, mem_delta: int = 0):
        """
        扣除资源
        :param cpu_delta: >0(扣除)； <0(释放)
        :param mem_delta: >0(扣除)； <0(释放)
        """
        if cpu_delta == mem_delta == 0:
            return True

        filters = {}
        updates = {}
        if cpu_delta != 0:
            filters['vcpu_total__gte'] = F('vcpu_allocated') + cpu_delta
            updates['vcpu_allocated'] = F('vcpu_allocated') + cpu_delta
        if mem_delta != 0:
            filters['mem_total__gte'] = F('mem_allocated') + mem_delta
            updates['mem_allocated'] = F('mem_allocated') + mem_delta

        try:
            r = Host.objects.filter(id=self.id, **filters).update(**updates)
        except Exception as e:
            return False

        if r <= 0:
            return False

        try:
            self.refresh_from_db()
        except:
            pass

        return True

    def user_has_perms(self, user):
        """
        用户是否有访问此宿主机的权限
        :param user: 用户
        :return:
            True    # has
            False   # no
        """
        if self.group.user_has_perms(user=user):
            return True

        return False

    def vm_created_num_add_1(self, commit=True):
        """
        已创建虚拟机数量+1
        :param commit: True,立即提交更新到数据库；False,不提交
        :return:
            True
            False
        """
        self.vm_created = F('vm_created') + 1
        if not commit:
            return True

        try:
            self.save(update_fields=['vm_created'])
            self.refresh_from_db()
        except Exception:
            return False

        return True

    def vm_created_num_sub_1(self, commit=True):
        """
        已创建虚拟机数量-1
        :param commit: True,立即提交更新到数据库；False,不提交
        :return:
            True
            False
        """
        self.vm_created = F('vm_created') - 1
        if not commit:
            return True

        try:
            self.save(update_fields=['vm_created'])
            self.refresh_from_db()
        except Exception:
            return False

        return True

    def stats_vcpu_mem_vms_now(self):
        """
        实时从数据库统计此宿主机下的所有虚拟机的总vcpu数量、总内存大小和总虚拟机数

        :return: dict
            {'vcpu': int, 'mem': int, 'vm_num': int}       # success
            {'vcpu': -1, 'mem': -1, 'vm_num': -1}          # error
        """
        from vms.models import Vm

        if hasattr(self, '_stats_now_data'):  # 缓存
            return self._stats_now_data

        err_ret = {'vcpu': -1, 'mem': -1, 'vm_num': -1}
        if not self.id:
            return err_ret
        try:
            a = Vm.objects.filter(host=self.id, vm_status='normal').aggregate(vcpu_now=Sum('vcpu'), mem_now=Sum('mem'), count=Count('pk'))
        except Exception:
            return err_ret

        vcpu_now = a.get('vcpu_now', -1)
        if not isinstance(vcpu_now, int):
            vcpu_now = 0

        mem_now = a.get('mem_now', -1)
        if not isinstance(mem_now, int):
            mem_now = 0

        count = a.get('count', -1)
        if not isinstance(count, int):
            count = 0

        self._stats_now_data = {'vcpu': vcpu_now, 'mem': mem_now, 'vm_num': count}
        return self._stats_now_data

    def save(self, *args, **kwargs):
        if self.pcserver:
            self.ipv4 = self.pcserver.host_ipv4
            self.real_cpu = self.pcserver.real_cpu
            self.real_mem = self.pcserver.real_mem

        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        if self.ipv4 == '127.0.0.1':
            raise ComputeError(msg='127.0.0.1为镜像专用宿主机，不能删除')
        super().delete(using=using, keep_parents=keep_parents)
