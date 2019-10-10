import os

from django.db import models
from django.db.models import Q, F
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from utils.ceph.manages import RbdManager, RadosError


#获取用户模型
User = get_user_model()

class CephCluster(models.Model):
    '''
    Ceph集群相关配置信息的模型
    '''
    id = models.AutoField(primary_key=True)
    uuid = models.CharField(verbose_name='xml中ceph的uuid', max_length=50, help_text='xml中ceph配置的uuid,libvirt通过uuid获取访问ceph的用户key')
    name = models.CharField(verbose_name='名称', max_length=100, unique=True)
    config       = models.TextField(verbose_name='ceph集群配置文本', default='')
    config_file  = models.CharField(max_length=200, editable=False, blank=True, verbose_name='配置文件保存路径', help_text="点击保存，配置文本会存储到这个文件, 此字段自动填充")
    keyring      = models.TextField(verbose_name='ceph集群keyring文本')
    keyring_file = models.CharField(max_length=200, editable=False, blank=True, verbose_name='keyring文件保存路径', help_text="点击保存，keyring文本会存储到这个文件, 此字段自动填充")
    hosts_xml = models.TextField(verbose_name='ceph monitors', null=True, help_text="设置虚机xml中disk/source元素的ceph monitors信息，格式:&lt;host name='10.100.50.1' port='6789'/&gt;")
    username = models.CharField(verbose_name='ceph用户名', max_length=100, default='admin', help_text="ceph用户名，需与keyring文件一致")

    class Meta:
        ordering = ('id',)
        verbose_name = 'CEPH集群配置'
        verbose_name_plural = '01_CEPH集群配置'

    def __str__(self):
        return self.name

    def get_config_file(self):
        '''
        ceph配置文件路径
        :return: str
        '''
        if not self.config_file:
            self._save_config_to_file()

        return self.config_file

    def get_keyring_file(self):
        '''
        ceph keyring文件路径
        :return: str
        '''
        if not self.keyring_file:
            self._save_config_to_file()

        return self.keyring_file

    def _save_config_to_file(self):
        '''
        ceph的配置内容保存到配置文件

        :return:
            True    # success
            False   # failed
        '''
        path = os.path.join(settings.BASE_DIR, 'data/ceph/conf/')
        if not self.config_file:
            self.config_file = os.path.join(path, f'{self.name}.conf')
        if not self.keyring_file:
            self.keyring_file = os.path.join(path, f'{self.name}.keyring')

        try:
            # 目录路径不存在存在则创建
            os.makedirs(path, exist_ok=True)

            with open(self.config_file, 'w') as f:
                f.write(self.config)

            with open(self.keyring_file, 'w') as f:
                f.write(self.keyring)
        except Exception:
            return False

        return True

    def save(self, *args, **kwargs):
        self._save_config_to_file()
        super().save(*args, **kwargs)


class CephPool(models.Model):
    '''
    CEPH pool
    '''
    id = models.AutoField(primary_key=True)
    pool_name = models.CharField(verbose_name='POOL名称', max_length=100)
    ceph = models.ForeignKey(to=CephCluster, on_delete=models.CASCADE)
    enable = models.BooleanField(default=True, verbose_name='是否启用')
    remarks = models.CharField(max_length=255, default='', blank=True, verbose_name='备注')

    class Meta:
        ordering = ('id',)
        verbose_name = 'CEPH pool'
        verbose_name_plural = '02_CEPH pool'

    def __str__(self):
        return f'ceph<{self.ceph.name}>@pool<{self.pool_name}>'


class Center(models.Model):
    '''
    分中心模型
    一个分中心对应一个存储后端，存储虚拟机相关的数据，Ceph集群，虚拟机的虚拟硬盘和系统镜像使用ceph块存储
    '''
    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name='数据中心名称', max_length=100, unique=True)
    location = models.CharField(verbose_name='位置', max_length=100)
    desc = models.CharField(verbose_name='简介', max_length=200, default='', blank=True)
    ceph_clusters = models.ManyToManyField(to=CephCluster, verbose_name='存储后端')

    class Meta:
        ordering = ('id',)
        verbose_name = '分中心'
        verbose_name_plural = '03_分中心'

    def __str__(self):
        return self.name


class Group(models.Model):
    '''
    宿主机组模型

    组用于权限隔离，某一个用户创建的虚拟机只能创建在指定的组的宿主机上，无权使用其他组的宿主机
    '''
    id = models.AutoField(primary_key=True)
    center = models.ForeignKey(Center, on_delete=models.CASCADE, verbose_name='组所属的分中心')
    name = models.CharField(max_length=100, verbose_name='组名称')
    desc = models.CharField(max_length=200, default='', blank=True, verbose_name='描述')
    users = models.ManyToManyField(to=User, blank=True)     # 有权访问此组的用户

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('id',)
        verbose_name = '宿主机组'
        verbose_name_plural = '04_宿主机组'
        unique_together = ('center', 'name')


class Vlan(models.Model):
    '''
    虚拟局域网子网模型
    '''
    PRIVATE = 0
    PUBLIC = 1
    VLAN_TYPE_CHOICES = (
        (PRIVATE, '私网'),
        (PUBLIC, '公网')
    )

    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name='VLAN名称', max_length=100)
    br = models.CharField(verbose_name='网桥', max_length=50)
    type = models.SmallIntegerField(verbose_name='网络类型', choices=VLAN_TYPE_CHOICES, default=PRIVATE)
    subnet_ip = models.GenericIPAddressField(verbose_name='子网IP')
    net_mask = models.GenericIPAddressField(verbose_name='子网掩码', null=True, blank=True)
    gateway = models.GenericIPAddressField(verbose_name='网关', null=True, blank=True)
    dns_server = models.GenericIPAddressField(verbose_name='DNS服务IP', null=True, blank=True)
    enable = models.BooleanField(verbose_name='状态', default=True)
    remarks = models.TextField(verbose_name='备注', default='', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('id',)
        verbose_name = 'VLAN子网'
        verbose_name_plural = '05_VLAN子网'


class MacIP(models.Model):
    '''
    IP地址模型

    分配给虚拟机的IP地址
    '''
    id = models.AutoField(primary_key=True)
    vlan = models.ForeignKey(to=Vlan, on_delete=models.SET_NULL, null=True, verbose_name='VLAN子网') # IP所属的vlan局域子网
    mac = models.CharField(verbose_name='MAC地址', max_length=17, unique=True)
    ipv4 = models.GenericIPAddressField(verbose_name='IP地址', unique=True)
    used = models.BooleanField(verbose_name='被使用', default=False, help_text='是否已分配给虚拟机使用')
    enable = models.BooleanField(verbose_name='开启使用', default=True, help_text='是否可以被分配使用')
    desc = models.TextField(verbose_name='备注说明', default='', blank=True)

    def __str__(self):
        return self.ipv4

    class Meta:
        verbose_name = 'IP地址'
        verbose_name_plural = '07_IP地址'

    def can_used(self):
        '''
        是否是自由的，可被使用的
        :return:
            True: 可使用
            False: 已被使用，或未开启使用
        '''
        if not self.used and self.enable:
            return True
        return False

    @classmethod
    def get_all_free_ip_in_vlan(self, vlan_id:int):
        '''
        获取一个vlan子网中 未被使用的 可分配的 所有ip
        :param vlan_id: 子网ID
        :return:
            QuerySet()
        '''
        return self.objects.filter(vlan=vlan_id, used=False, enable=True).all()

    def set_in_used(self, auto_commit=True):
        '''
        设置ip被使用中

        :param auto_commit: True:立即更新到数据库；False: 不更新到数据库
        :return:
            True    # 成功
            False   # 失败
        '''
        if not auto_commit:
            self.used = True
            return True

        try:
            r = self.objects.filter(id=self.id, used=False).update(used=True)  # 乐观锁方式,
        except Exception as e:
            return False
        if r > 0:  # 更新行数
            self.used = True
            return True

        return False

    def set_free(self, auto_commit=True):
        '''
        释放ip

        :param auto_commit: True:立即更新到数据库；False: 不更新到数据库
        :return:
            True    # 成功
            False   # 失败
        '''
        self.used = False
        if not auto_commit:
            return True

        try:
            self.save(update_fields=['used'])
        except Exception as e:
            return False

        return True



class Host(models.Model):
    '''
    宿主机模型

    宿主机是真实的物理主机，是虚拟机的载体，虚拟机使用宿主机的资源在宿主机上运行
    一台宿主机可能连接多个vlan子网
    '''
    id = models.AutoField(primary_key=True)
    group = models.ForeignKey(to=Group, on_delete=models.CASCADE, verbose_name='宿主机所属的组')
    vlans = models.ManyToManyField(to=Vlan, verbose_name='VLAN子网', related_name='vlan_hosts') # 局域子网
    ipv4 = models.GenericIPAddressField(unique=True, verbose_name='宿主机ip')
    vcpu_total = models.IntegerField(default=24, verbose_name='宿主机CPU总数')
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

    def __str__(self):
        return self.ipv4

    class Meta:
        verbose_name = '宿主机'
        verbose_name_plural = '06_宿主机'

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
        self.vcpu_allocated = F('vcpu_allocated') + vcpu
        self.mem_allocated = F('mem_allocated') + mem
        try:
            self.save()
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
        self.vcpu_allocated = F('vcpu_allocated') - vcpu
        self.mem_allocated = F('mem_allocated') - mem
        try:
            self.save()
        except Exception as e:
            return False

        return True


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
    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name='镜像名称', max_length=100)
    version = models.CharField(verbose_name='系统版本信息', max_length=100)
    type = models.ForeignKey(to=ImageType, on_delete=models.CASCADE, verbose_name='类型')
    ceph_pool = models.ForeignKey(to=CephPool, on_delete=models.CASCADE, verbose_name='CEPH存储后端')
    base_image = models.CharField(verbose_name='基础镜像', max_length=200, default='', help_text='用于创建镜像快照')
    enable = models.BooleanField(verbose_name='启用', default=True, help_text="若取消复选框，用户创建虚拟机时无法看到该镜像")
    create_newsnap = models.BooleanField('更新模板', default=False, help_text='''选中该选项，保存时会基于基础镜像"
           "创建新快照（以当前时间作为快照名称）,更新操作系统模板。新建snap时请确保基础镜像处于关机状态！''')  # 这个字段不需要持久化存储，用于获取用户页面选择
    snap = models.CharField(verbose_name='当前生效镜像快照', max_length=200, default='', blank=True, editable=True)
    xml_tpl = models.ForeignKey(to=VmXmlTemplate, on_delete=models.CASCADE, verbose_name='xml模板',
                                help_text='使用此镜象创建虚拟机时要使用的XML模板，不同类型的镜像有不同的XML格式')
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    desc = models.TextField(verbose_name='描述', default='', blank=True)

    def __str__(self):
        return self.snap

    class Meta:
        verbose_name = '操作系统镜像'
        verbose_name_plural = '10_操作系统镜像'
        unique_together = ('name', 'version')

    @property
    def fullname(self):
        return self.name + ' ' + self.version

    def save(self, *args, **kwargs):
        # super().save(*args, **kwargs)
        if self.create_newsnap:  # 用户选中创建snap复选框
            self._create_snap()

        super().save(*args, **kwargs)

    def _create_snap(self):
        '''
        从基image创建快照snap，
        :return:
            True    # success
            False   # failed
        '''
        ceph_pool = self.ceph_pool
        if not ceph_pool:
            return False
        pool_name = ceph_pool.pool_name
        config = ceph_pool.ceph
        if not config:
            return False

        config_file = config.get_config_file()
        keyring_file = config.get_keyring_file()

        now_timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        snap_name = f'{self.base_image}@{now_timestamp}'
        self.create_newsnap = False
        try:
            rbd = RbdManager(conf_file=config_file, keyring_file=keyring_file, pool_name=pool_name)
            rbd.create_snap(image_name=self.base_image, snap_name=snap_name)
        except RadosError as e:
            self.enable = False
            self.desc = f'创建快照{snap_name}失败：{str(e)}' + self.desc
        except Exception as e:
            self.enable = False
            self.desc = f'创建快照{snap_name}失败：{str(e)}' + self.desc
        else:
            self.snap = snap_name
            return True

        return False


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
        verbose_name_plural = '11_虚拟机'

    def get_uuid(self):
        if isinstance(self.uuid, str):
            return self.uuid
        return self.uuid.hex
