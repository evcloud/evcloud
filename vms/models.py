import os

from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model


#获取用户模型
User = get_user_model()

class CephConfig(models.Model):
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

    def save(self, *args, **kwargs):
        path = os.path.join(settings.BASE_DIR, 'data/ceph/conf/')
        if not self.config_file:
            self.config_file  = os.path.join(path, f'{self.name}.conf')
        if not self.keyring_file:
            self.keyring_file = os.path.join(path, f'{self.name}.keyring')

        # 目录路径不存在存在则创建
        os.makedirs(path, exist_ok=True)

        with open(self.config_file,'w') as f:
            f.write(self.config)

        with open(self.keyring_file,'w') as f:
            f.write(self.keyring)

        super().save(*args, **kwargs)


class CephBackend(models.Model):
    '''
    CEPH存储后端
    '''
    id = models.AutoField(primary_key=True)
    pool_name = models.CharField(verbose_name='POOL名称', max_length=100)
    ceph = models.ForeignKey(to=CephConfig, on_delete=models.CASCADE)

    class Meta:
        ordering = ('id',)
        verbose_name = 'CEPH存储后端'
        verbose_name_plural = '02_CEPH存储后端'

    def __str__(self):
        return f'ceph<{self.ceph.name}>@pool<{self.pool_name}>'


# class StorageBackend(models.Model):
#     '''
#     存储后端相关信息的模型， Ceph, Local(宿主机)
#     '''
#     BACKEND_CEPH = 0
#     BACKEND_LOCAL = 1
#
#     BACKEND_TYPE_CHOICES = (
#         (BACKEND_CEPH, 'CEPH'),
#         (BACKEND_LOCAL, 'LOCAL')
#     )
#
#     id = models.AutoField(primary_key=True)
#     name = models.CharField(verbose_name='名称', max_length=100, unique=True)
#     # type = models.SmallIntegerField(verbose_name='类型', choices=BACKEND_TYPE_CHOICES, default=BACKEND_CEPH)
#     backend = models.ForeignKey(to=CephBackend, on_delete=models.SET_NULL, null=True) # CEPH存储后端， 多对一关系
#
#     class Meta:
#         ordering = ('id',)
#         verbose_name = '存储后端'
#         verbose_name_plural = '存储后端'
#
#     def __str__(self):
#         return self.name


class Center(models.Model):
    '''
    分中心模型
    一个分中心对应一个存储后端，存储虚拟机相关的数据，Ceph集群，虚拟机的虚拟硬盘和系统镜像使用ceph块存储
    '''
    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name='数据中心名称', max_length=100, unique=True)
    location = models.CharField(verbose_name='位置', max_length=100)
    desc = models.CharField(verbose_name='简介', max_length=200, default='', blank=True)
    # backend = models.ForeignKey(to=StorageBackend, on_delete=models.SET_NULL, null=True) # 存储后端, 多对一关系
    backends = models.ManyToManyField(to=CephBackend, verbose_name='存储后端')

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
    enable = models.BooleanField(verbose_name='状态', default=True)
    desc = models.TextField(verbose_name='备注说明')

    def __str__(self):
        return self.ipv4

    class Meta:
        verbose_name = 'IP地址'
        verbose_name_plural = '07_IP地址'


class Host(models.Model):
    '''
    宿主机模型

    宿主机是真实的物理主机，是虚拟机的载体，虚拟机使用宿主机的资源在宿主机上运行
    一台宿主机可能连接多个vlan子网
    '''
    id = models.AutoField(primary_key=True)
    group = models.ForeignKey(to=Group, on_delete=models.CASCADE, verbose_name='宿主机所属的组')
    vlans = models.ManyToManyField(to=Vlan, verbose_name='VLAN子网') # 局域子网
    ipv4 = models.GenericIPAddressField(unique=True, verbose_name='宿主机ip')
    vcpu_total = models.IntegerField(default=24, verbose_name='宿主机CPU总数')
    vcpu_allocated = models.IntegerField(default=0, verbose_name='宿主机已分配CPU总数')
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
    base_image = models.CharField(verbose_name='基础镜像', max_length=200, default='', help_text='用于创建镜像快照')
    enable = models.BooleanField(verbose_name='启用', default=True, help_text="若取消复选框，用户创建虚拟机时无法看到该镜像")
    create_newsnap = models.BooleanField('更新模板', default=False, help_text='''选中该选项，保存时会基于基础镜像"
           "创建新快照（以当前时间作为快照名称）,更新操作系统模板。新建snap时请确保基础镜像处于关机状态！''')  # 这个字段不需要持久化存储，用于获取用户页面选择
    snap = models.CharField(verbose_name='当前生效镜像快照', max_length=200, default='')
    xml_tpl = models.ForeignKey(VmXmlTemplate, on_delete=models.CASCADE, verbose_name='xml模板',
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
        super().save(*args, **kwargs)
        # if not self.create_newsnap:  # 用户没有选中创建snap复选框
        #     super().save(*args, **kwargs)
        #     return True
        #
        # ceph_pool = self.cephpool
        # ceph_config_file = os.path.join(settings.BASE_DIR, ceph_pool.cephcluster.config_file)
        # ceph_keyring_file = os.path.join(settings.BASE_DIR, ceph_pool.cephcluster.keyring_file)
        # now_timestamp = timezone.localtime(timezone.now()).strftime("%Y%m%d_%H%M%S")
        # new_snap_name = self.base_image + '@' + now_timestamp
        # self.create_newsnap = False
        # self.snap = new_snap_name
        # try:
        #     from ceph.cephfunction import create_snap
        #     create_snap(ceph_config_file, ceph_keyring_file, ceph_pool.pool, new_snap_name);
        # except:
        #     self.snap = "ERROR_SNAP:  " + new_snap_name
        #     self.enable = False
        # finally:
        #     super().save(*args, **kwargs)


class Vm(models.Model):
    '''
    虚拟机模型
    '''
    uuid = models.UUIDField(verbose_name='虚拟机UUID', primary_key=True)
    name = models.CharField(verbose_name='名称', max_length=200)
    vcpu = models.IntegerField(verbose_name='CPU数')
    mem = models.IntegerField(verbose_name='内存大小')
    disk = models.CharField(verbose_name='系统盘名称', max_length=100, unique=True, help_text='vm自己的系统盘，保存于ceph中的rdb文件名称')
    image = models.ForeignKey(to=Image, on_delete=models.SET_NULL, null=True, verbose_name='源镜像', help_text='创建此虚拟机时使用的源系统镜像，disk从image复制')
    user = models.ForeignKey(to=User, verbose_name='创建者', on_delete=models.SET_NULL, related_name='user_vms',  null=True)
    create_time = models.DateTimeField(verbose_name='创建日期', auto_now_add=True)
    remarks = models.TextField(verbose_name='备注', default='', blank=True)

    host = models.ForeignKey(to=Host, on_delete=models.SET_NULL, verbose_name='宿主机', null=True)
    ceph = models.ForeignKey(to=CephBackend, on_delete=models.SET_NULL, verbose_name='CEPH存储后端', null=True)
    xml = models.TextField(verbose_name='虚拟机当前的XML', help_text='定义虚拟机的当前的XML内容')
    mac_ip = models.ForeignKey(to=MacIP, on_delete=models.SET_NULL, related_name='ip_vm', verbose_name='MAC IP', null=True)
    deleted     = models.BooleanField(verbose_name='删除', default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '虚拟机'
        verbose_name_plural = '11_虚拟机'
