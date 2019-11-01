from django.db import models

# Create your models here.

class NetworkType(models.Model):
    '''
    网络类型
    '''
    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name='类型名称', max_length=100)
    remarks = models.CharField(verbose_name='备注', max_length=255, default='', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('id',)
        verbose_name = '网络类型'
        verbose_name_plural = '05_网络类型'


class Vlan(models.Model):
    '''
    虚拟局域网子网模型
    '''
    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name='VLAN名称', max_length=100)
    br = models.CharField(verbose_name='网桥', max_length=50)
    net_type = models.ForeignKey(to=NetworkType, verbose_name='网络类型',on_delete=models.CASCADE, related_name='vlan_set')
    # center = models.ForeignKey(to=Center, verbose_name='所属分中心', on_delete=models.CASCADE, related_name='vlan_set')
    subnet_ip = models.GenericIPAddressField(verbose_name='子网IP')
    net_mask = models.GenericIPAddressField(verbose_name='子网掩码')
    gateway = models.GenericIPAddressField(verbose_name='网关')
    dns_server = models.GenericIPAddressField(verbose_name='DNS服务IP')
    dhcp_config = models.TextField(verbose_name='DHCP部分配置信息')
    enable = models.BooleanField(verbose_name='状态', default=True)
    remarks = models.TextField(verbose_name='备注', default='', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('id',)
        verbose_name = 'VLAN子网'
        verbose_name_plural = '05_VLAN子网'

    def get_free_ip_number(self):
        '''
        获得该子网已经生成，但尚未使用的ip数量
        :return: int
        '''
        return MacIP.objects.filter(id=self, used=False, enable=True).count()

    def get_ip_number(self):
        '''
        获得该子网已经生成的所有ip数量
        :return: int
        '''
        return MacIP.objects.filter(id=self, enable=True).count()


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

    class Meta:
        verbose_name = 'MAC IP地址'
        verbose_name_plural = '07_MAC IP地址'

    def __str__(self):
        return self.ipv4

    def get_detail_str(self):
        return f'id={self.id};mac={self.mac};ipv4={self.ipv4};'

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
        if self.used == False:
            return True

        self.used = False
        if not auto_commit:
            return True

        try:
            self.save(update_fields=['used'])
        except Exception as e:
            return False

        return True

