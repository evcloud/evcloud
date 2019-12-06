from django.db import transaction
from django.db.models import Sum

from compute.models import Center, Group, Host
from network.models import Vlan
from image.models import Image
from ceph.models import CephPool


class ComputeError(Exception):
    '''
    计算资源相关错误定义
    '''
    def __init__(self, code:int=0, msg:str='', err=None):
        '''
        :param code: 错误码
        :param msg: 错误信息
        :param err: 错误对象
        '''
        self.code = code
        self.msg = msg
        self.err = err

    def __str__(self):
        return self.detail()

    def detail(self):
        '''错误详情'''
        if self.msg:
            return self.msg

        if self.err:
            return str(self.err)

        return '未知的错误'


class DefaultSum(Sum):
    '''
    累加结果为None时，返回默认值
    '''
    def __init__(self, *expressions, distinct=False, filter=None, return_if_none=0, **extra):
        self.return_if_none = return_if_none
        super().__init__(*expressions, distinct=distinct, filter=filter, **extra)

    def convert_value(self, value, expression, connection):
        return self.return_if_none if value is None else value


class CenterManager:
    '''
    分中心管理器
    '''
    def get_center_by_id(self, center_id:int):
        '''
        通过id获取分中心

        :param center_id: 分中心id
        :return:
            Image() # success
            None    #不存在
        :raise ComputeError
        '''
        if not isinstance(center_id, int) or center_id < 0:
            raise ComputeError(msg='分中心ID参数有误')

        try:
            return Center.objects.filter(id=center_id).first()
        except Exception as e:
            raise ComputeError(msg=f'查询分中心时错误,{str(e)}')

    def get_group_ids_by_center(self, center_or_id):
        '''
        获取分中心下的宿主机组id list

        :param center_or_id: 分中心对象或id
        :return:
            ids: list   # success
        :raise ComputeError
        '''
        if isinstance(center_or_id, int):
            if center_or_id <= 0:
                raise ComputeError(msg='无效的center id')
            center = self.get_center_by_id(center_id=center_or_id)
            if not center:
                raise ComputeError(msg='指定的分中心不存在')
        elif not isinstance(center_or_id, Center):
            raise ComputeError(msg='无效的center or id')
        else:
            center = center_or_id

        ids = list(center.group_set.values_list('id', flat=True).all())
        return ids

    def get_center_queryset(self):
        return Center.objects.all()

    def get_group_queryset_by_center(self, center_or_id):
        '''
        获取分中心下的宿主机组查询集

        :param center_or_id: 分中心对象或id
        :return:
            groups: QuerySet   # success
        :raise ComputeError
        '''
        if isinstance(center_or_id, int):
            if center_or_id <= 0:
                raise ComputeError(msg='无效的center id')
            center = self.get_center_by_id(center_id=center_or_id)
            if not center:
                raise ComputeError(msg='指定的分中心不存在')
        elif not isinstance(center_or_id, Center):
            raise ComputeError(msg='无效的center or id')
        else:
            center = center_or_id

        return center.group_set.all()

    def get_user_group_queryset(self, user):
        '''
        获取用户有权限的宿主机组查询集

        :param user: 用户对象
        :return:
            groups: QuerySet   # success
        '''
        if user.is_superuser:
            return Group.objects.all()

        return user.group_set.all()

    def get_user_group_queryset_by_center(self, center_or_id, user):
        '''
        获取分中心下的宿主机组查询集

        :param center_or_id: 分中心对象或id
        :param user: 用户对象
        :return:
            groups: QuerySet   # success
        :raise ComputeError
        '''
        if isinstance(center_or_id, Center) or isinstance(center_or_id, int):
            qs = self.get_user_group_queryset(user)
            return qs.filter(center=center_or_id)

        raise ComputeError(msg='无效的center id')

    def get_ceph_queryset_by_center(self, center_or_id):
        '''
        获取一个分中心下的所有ceph集群查询集

        :param center_or_id: 分中心对象或id
        :return:
             QuerySet   # success
        :raise ComputeError
        '''
        if isinstance(center_or_id, int):
            if center_or_id <= 0:
                raise ComputeError(msg='无效的center id')
            center = self.get_center_by_id(center_id=center_or_id)
            if not center:
                raise ComputeError(msg='指定的分中心不存在')
        elif not isinstance(center_or_id, Center):
            raise ComputeError(msg='无效的center or id')
        else:
            center = center_or_id

        return center.ceph_clusters.all()

    def get_ceph_ids_by_center(self, center_or_id):
        '''
        获取一个分中心下的所有ceph集群id list

        :param center_or_id: 分中心对象或id
        :return:
            ids: list   # success
        :raise ComputeError
        '''
        cephs = self.get_ceph_queryset_by_center(center_or_id)
        ids = list(cephs.values_list('id', flat=True).all())
        return ids

    def get_pool_queryset_by_center(self, center_or_id):
        '''
        获取一个分中心下的所有ceph pool查询集

        :param center_or_id: 分中心对象或id
        :return:
             QuerySet   # success
        :raise ComputeError
        '''
        ceph_ids = self.get_ceph_ids_by_center(center_or_id)
        return CephPool.objects.filter(ceph__in=ceph_ids, enable=True).all()

    def get_pool_ids_by_center(self, center_or_id):
        '''
        获取一个分中心下的所有ceph pool id

        :param center_or_id: 分中心对象或id
        :return:
             QuerySet   # success
        :raise ComputeError
        '''
        pools = self.get_pool_queryset_by_center(center_or_id)
        return list(pools.values_list('id', flat=True).all())

    def get_stat_center_queryset(self, filter:dict=None):
        '''
        分中心资源统计查询集

        :param filter: center的过滤条件
        :return:
            QuerySet   # success
        '''
        qs = Center.objects.all()
        if filter:
            qs = qs.filter(**filter).all()
        return qs.annotate(
            mem_total=DefaultSum('group_set__hosts_set__mem_total'),
            mem_allocated=DefaultSum('group_set__hosts_set__mem_allocated'),
            mem_reserved=DefaultSum('group_set__hosts_set__mem_reserved'),
            vcpu_total=DefaultSum('group_set__hosts_set__vcpu_total'),
            vcpu_allocated=DefaultSum('group_set__hosts_set__vcpu_allocated'),
            vm_created=DefaultSum('group_set__hosts_set__vm_created')).all()


class GroupManager:
    '''
    宿主机组管理器
    '''
    def get_group_by_id(self, group_id:int):
        '''
        通过id获取宿主机组

        :param group_id: 宿主机组id
        :return:
            Group() # success
            None    #不存在
        :raise ComputeError
        '''
        if not isinstance(group_id, int) or group_id < 0:
            raise ComputeError(msg='宿主机组ID参数有误')

        try:
            return Group.objects.filter(id=group_id).first()
        except Exception as e:
            raise ComputeError(msg=f'查询宿主机组时错误,{str(e)}')

    def get_host_queryset_by_group(self, group_or_id):
        '''
        通过宿主机组对象和id获取宿主机查询集

        :param group_or_id: 宿主机组对象和id
        :return:
            QuerySet   # success
        :raise ComputeError
        '''
        if isinstance(group_or_id, int):
            if group_or_id <= 0:
                raise ComputeError(msg='无效的group id')
            group = self.get_group_by_id(group_or_id)
        elif not isinstance(group_or_id, Group):
            raise ComputeError(msg='无效的group or id')
        else:
            group = group_or_id

        return group.hosts_set.filter(enable=True).all()

    def get_host_ids_by_group(self,  group_or_id):
        '''
        通过宿主机组对象和id获取宿主机id list

        :param group_or_id: 宿主机组对象和id
        :return:
            ids: list   # success
        :raise ComputeError
        '''
        hosts = self.get_host_queryset_by_group(group_or_id)

        try:
            ids = list(hosts.values_list('id', flat=True).all())
        except Exception as e:
            raise ComputeError(msg=f'查询宿主机id错误，{str(e)}')
        return ids

    def get_hsot_queryset_by_group_ids(self, ids:list):
        '''
        通过宿主机组id list获取宿主机查询集

        :param ids: 宿主机组id list
        :return:
            QuerySet   # success
        '''
        return Host.objects.filter(group__in=ids).all()

    def get_hsot_ids_by_group_ids(self, ids:list):
        '''
        通过宿主机组id list获取宿主机id list

        :param ids: 宿主机组id list
        :return:
            ids: list   # success
        :raise ComputeError
        '''
        hosts = self.get_hsot_queryset_by_group_ids(ids)
        try:
            ids = list(hosts.values_list('id', flat=True).all())
        except Exception as e:
            raise ComputeError(msg=f'查询宿主机id错误，{str(e)}')
        return ids

    def get_hsot_ids_by_group_or_ids(self, group_or_ids):
        '''
        通过宿主机组对象或id,或id list获取宿主机id list

        :param group_or_ids: 宿主机组对象，id,或id list
        :return:
            ids: list   # success
        :raise ComputeError
        '''
        if isinstance(group_or_ids, list):
            return self.get_hsot_ids_by_group_ids(group_or_ids)
        elif isinstance(group_or_ids, int) or isinstance(group_or_ids, Group):
            return self.get_host_ids_by_group(group_or_ids)

        raise ComputeError(msg='无效的宿主机组参数')

    def get_stat_group_wueryset(self, filter:dict=None):
        '''
        资源统计宿主机组查询集

        :param filter: group的过滤条件
        :return:
            QuerySet()
        '''
        qs = Group.objects.all()
        if filter:
            qs = qs.filter(**filter).all()

        return qs.select_related('center').annotate(
            mem_total=DefaultSum('hosts_set__mem_total'), mem_allocated=DefaultSum('hosts_set__mem_allocated'),
            vcpu_total=DefaultSum('hosts_set__vcpu_total'), vcpu_allocated=DefaultSum('hosts_set__vcpu_allocated'),
            mem_reserved=DefaultSum('hosts_set__mem_reserved'),vm_created=DefaultSum('hosts_set__vm_created')).all()


class HostManager:
    '''
    宿主机管理器
    '''
    def get_host_by_id(self, host_id:int):
        '''
        通过id获取宿主机元数据模型对象

        :param host_id: 宿主机id
        :return:
            Host() # success
            None    #不存在
        :raise ComputeError
        '''
        if not isinstance(host_id, int) or host_id < 0:
            raise ComputeError(msg='宿主机ID参数有误')

        try:
            return Host.objects.filter(id=host_id).first()
        except Exception as e:
            raise ComputeError(msg=f'查询宿主机时错误,{str(e)}')

    def get_hosts_by_group_id(self, group_id:int):
        '''
        获取宿主机组的所有宿主机元数据模型对象

        :param group_id: 宿主机组id
        :return:
            [Host(),]    # success
            raise ComputeError #发生错误

        :raise ComputeError
        '''
        if not isinstance(group_id, int) or group_id < 0:
            raise ComputeError(msg='宿主机组ID参数有误')
        try:
            hosts_qs = Host.objects.filter(group=group_id).all()
            return list(hosts_qs)
        except Exception as e:
            raise ComputeError(msg=f'查询宿主机组的宿主机列表时错误,{str(e)}')

    def filter_hosts_queryset(self, group_id:int=0, vlan_id:int=0, enable:bool=True):
        '''
        过滤宿主机查询集

        :param group_id: 宿主机组id，默认为0，忽略此参数
        :param vlan_id: 子网网段id，默认为0，忽略此参数
        :param enable: True,过滤有效的宿主机；False，不过滤
        :return:
            QuerySet    # success

        :raises: ComputeError
        '''
        if group_id < 0 or vlan_id < 0:
            raise ComputeError(msg='group_id或vlan_id无效')

        qs = None
        if vlan_id > 0:
            vlan = Vlan.objects.filter(id=vlan_id).first()
            qs = vlan.vlan_hosts.all()

        if group_id > 0:
            if qs is not None:
                qs = qs.filter(group=group_id).all()
            else:
                qs = Host.objects.filter(group=group_id).all()

        if qs is None:
            qs = Host.objects.all()

        if enable == True:
            qs = qs.filter(enable=True).all()

        return qs

    def get_hosts_queryset_by_group_vlan(self, group_or_id, vlan:Vlan):
        '''
        获取宿指定主机组，并且包含指定vlan的所有宿主机元数据模型对象查询集

        :param group_or_id: 宿主机组对象Group()或id
        :param vlan: 子网对象
        :return:
            QuerySet    # success
            raise ComputeError #发生错误

        :raise ComputeError
        '''
        if isinstance(group_or_id, Group):
            group = group_or_id
        elif isinstance(group_or_id, int) and group_or_id > 0:
            group = group_or_id
        else:
            raise ComputeError(msg='请输入一个宿主机组对象或宿主机组ID')

        if not isinstance(vlan, Vlan):
            raise ComputeError(msg='请输入一个子网Vlan对象')

        return  vlan.vlan_hosts.filter(group=group, enable=True).all()

    def get_hosts_by_group_and_vlan(self, group_or_id, vlan:Vlan):
        '''
        获取宿指定主机组，并且包含指定vlan的所有宿主机元数据模型对象

        :param group_or_id: 宿主机组对象Group()或id
        :param vlan: 子网对象
        :return:
            [Host(),]    # success
            raise ComputeError #发生错误

        :raise ComputeError
        '''
        hosts_qs = self.get_hosts_queryset_by_group_vlan(group_or_id=group_or_id, vlan=vlan)
        try:
            return list(hosts_qs)
        except Exception as e:
            raise ComputeError(msg=f'查询宿主机组的宿主机列表时错误,{str(e)}')

    def claim_from_host(self, host_id:int, vcpu:int, mem:int):
        '''
        向宿主机申请资源

        :param host_id: 宿主机id
        :param vcpu: 要申请的cpu数
        :param mem: 要申请的内存大小
        :return:
            Host()  # success
            None    #宿主机不存在，或没有足够的资源
        :raise ComputeError
        '''
        with transaction.atomic():
            host = Host.objects.select_for_update().filter(id=host_id).first()
            if not host:
                return None

            # 宿主机是否满足资源需求
            if not host.meet_needs(vcpu=vcpu, mem=mem):
                raise ComputeError(msg='宿主机没有足够的资源')

            # 申请资源
            if not host.claim(vcpu=vcpu, mem=mem):
                raise ComputeError(msg='向宿主机申请资源时失败')

        return host

    def free_to_host(self, host_id: int, vcpu: int, mem: int):
        '''
        释放从宿主机申请的资源

        :param host_id: 宿主机id
        :param vcpu: 要申请的cpu数
        :param mem: 要申请的内存大小
        :return:
            True    # success
            False   # failed
        '''
        # 释放资源
        host = Host.objects.filter(id=host_id).first()
        if not host:
            return False

        return host.free(vcpu=vcpu, mem=mem)

    def filter_meet_requirements(self, hosts:list, vcpu:int, mem:int, claim=False):
        '''
        筛选满足申请资源要求的宿主机

        :param hosts: 宿主机列表
        :param vcpu: 要申请的cpu数
        :param mem: 要申请的内存大小
        :param claim: True:立即申请资源
        :return:
            Host()  # success
            None    # 没有足够的资源的宿主机

        :raise ComputeError
        '''
        # 检查参数
        if not isinstance(hosts, list):
            raise ComputeError(msg='参数有误，请输入宿主机列表')

        if len(hosts) == 0: # 没有满足条件的宿主机
            return None

        if not isinstance(hosts[0], Host):
            raise ComputeError(msg='参数有误，请输入宿主机列表')

        if not isinstance(vcpu, int) or vcpu <= 0:
            raise ComputeError(msg='参数有误，vcpu必须是一个正整数')

        if not isinstance(mem, int) or mem <= 0:
            raise ComputeError(msg='参数有误，mem必须是一个正整数')

        for host in hosts:
            # 宿主机是否满足资源需求
            if not host.meet_needs(vcpu=vcpu, mem=mem):
                continue

            if not claim: # 立即申请资源
                continue

            host = self.claim_from_host(host_id=host.id, vcpu=vcpu, mem=mem)
            if host:
                return host

        return None


