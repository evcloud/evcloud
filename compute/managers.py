import random

from django.db import transaction
from django.db.models import Sum
from django.utils.functional import cached_property

from compute.models import Center, Group, Host
from ceph.models import CephPool
from utils.errors import ComputeError


class DefaultSum(Sum):
    """
    累加结果为None时，返回默认值, 只是用于int和float
    """
    def __init__(self, *expressions, distinct=False, filter=None, return_if_none=0, **extra):
        self.return_if_none = return_if_none
        super().__init__(*expressions, distinct=distinct, filter=filter, **extra)

    @cached_property
    def convert_value(self):
        """
        Expressions provide their own converters because users have the option
        of manually specifying the output_field which may be a different type
        from the one the database returns.
        """
        field = self.output_field
        internal_type = field.get_internal_type()
        if internal_type == 'FloatField':
            return lambda value, expression, connection: self.return_if_none if value is None else float(value)
        elif internal_type.endswith('IntegerField'):
            return lambda value, expression, connection: self.return_if_none if value is None else int(value)
        # elif internal_type == 'DecimalField':
        #     return lambda value, expression, connection: self.return_if_none if value is None else Decimal(value)
        return self._convert_value_noop


class CenterManager:
    """
    分中心管理器
    """
    def __init__(self):
        # 分中心对象缓存，分中心对象数据有变化，需要清除缓存或设置覆盖缓存
        self._cache_centers = {}

    def _cache_center_remove(self, center_id=None):
        """
        尝试从分中心对象缓存移除指定的分中心对象，未指定center_id，清除所有缓存

        :param center_id: 分中心id
        """
        if center_id is None:
            self._cache_centers.clear()
        self._cache_centers.pop(center_id, None)

    def _cache_center_add(self, center):
        """
        缓存一个分中心对象

        :param center: 分中心对象
        """
        if not isinstance(center, Center):
            return

        cid = center.id
        if cid:
            self._cache_centers[cid] = center

    def _cache_center_get(self, center_id):
        """
        尝试从分中心对象缓存获取分中心对象

        :return:
            Center() or None
        """
        c = self._cache_centers.get(center_id, None)
        if c and isinstance(c, Center):
            return c
        return None

    @staticmethod
    def get_center_by_id(center_id: int):
        """
        通过id获取分中心

        :param center_id: 分中心id
        :return:
            Image() # success
            None    #不存在
        :raise ComputeError
        """
        if not isinstance(center_id, int) or center_id < 0:
            raise ComputeError(msg='分中心ID参数有误')

        try:
            return Center.objects.filter(id=center_id).first()
        except Exception as e:
            raise ComputeError(msg=f'查询分中心时错误,{str(e)}')

    def enforce_center_obj(self, center_or_id):
        """
        转换为分中心对象

        :param center_or_id: Center() or id
        :return:
            Center()

        :raise: ComputeError    # 分中心不存在，或参数有误
        """
        if isinstance(center_or_id, Center):
            return center_or_id

        if isinstance(center_or_id, int):
            if center_or_id <= 0:
                raise ComputeError(msg='无效的center id')

            c = self._cache_center_get(center_or_id)
            if c:
                return c

            c = self.get_center_by_id(center_or_id)
            if c:
                self._cache_center_add(c)
                return c
            else:
                raise ComputeError(msg='分中心不存在')

        raise ComputeError(msg='无效的center or id')

    def get_group_ids_by_center(self, center_or_id):
        """
        获取分中心下的宿主机组id list

        :param center_or_id: 分中心对象或id
        :return:
            ids: list   # success
        :raise ComputeError
        """
        center = self.enforce_center_obj(center_or_id)
        ids = list(center.group_set.values_list('id', flat=True).all())
        return ids

    @staticmethod
    def get_center_queryset():
        return Center.objects.all()

    def get_group_queryset_by_center(self, center_or_id):
        """
        获取分中心下的宿主机组查询集

        :param center_or_id: 分中心对象或id
        :return:
            groups: QuerySet   # success
        :raise ComputeError
        """
        center = self.enforce_center_obj(center_or_id)
        return center.group_set.all()

    @staticmethod
    def get_user_group_queryset(user):
        """
        获取用户有权限的宿主机组查询集

        :param user: 用户对象
        :return:
            groups: QuerySet   # success
        """
        if user.is_superuser:
            return Group.objects.all()

        return user.group_set.all()

    def get_user_group_ids(self, user):
        """
        获取用户有权限的宿主机组id list

        :param user: 用户对象
        :return:
            ids: list   # success

        :raise ComputeError
        """
        qs = self.get_user_group_queryset(user=user)
        try:
            ids = list(qs.values_list('id', flat=True).all())
        except Exception as e:
            raise ComputeError(msg=f'查询宿主机组id错误，{str(e)}')
        return ids

    def get_user_group_queryset_by_center(self, center_or_id, user):
        """
        获取分中心下的宿主机组查询集

        :param center_or_id: 分中心对象或id
        :param user: 用户对象
        :return:
            groups: QuerySet   # success
        :raise ComputeError
        """
        if isinstance(center_or_id, Center) or isinstance(center_or_id, int):
            qs = self.get_user_group_queryset(user)
            return qs.filter(center=center_or_id)

        raise ComputeError(msg='无效的center id')

    def get_user_group_ids_by_center(self, center, user):
        """
        获取分中心下的，用户有访问权限的宿主机组查询集

        :param center: 分中心对象或ID
        :param user: 用户对象
        :return:
            QuerySet()
        """
        qs = self.get_user_group_queryset_by_center(center_or_id=center, user=user)
        try:
            ids = list(qs.values_list('id', flat=True).all())
        except Exception as e:
            raise ComputeError(msg=f'查询宿主机组id错误，{str(e)}')
        return ids

    def get_ceph_queryset_by_center(self, center_or_id):
        """
        获取一个分中心下的所有ceph集群查询集

        :param center_or_id: 分中心对象或id
        :return:
             QuerySet   # success
        :raise ComputeError
        """
        center = self.enforce_center_obj(center_or_id)
        return center.ceph_clusters.all()

    def get_ceph_ids_by_center(self, center_or_id):
        """
        获取一个分中心下的所有ceph集群id list

        :param center_or_id: 分中心对象或id
        :return:
            ids: list   # success
        :raise ComputeError
        """
        cephs = self.get_ceph_queryset_by_center(center_or_id)
        ids = list(cephs.values_list('id', flat=True).all())
        return ids

    def get_pool_queryset_by_center(self, center_or_id):
        """
        获取一个分中心下的所有ceph pool查询集

        :param center_or_id: 分中心对象或id
        :return:
             QuerySet   # success
        :raise ComputeError
        """
        ceph_ids = self.get_ceph_ids_by_center(center_or_id)
        return CephPool.objects.filter(ceph__in=ceph_ids, enable=True).all()

    def get_pool_ids_by_center(self, center_or_id):
        """
        获取一个分中心下的所有ceph pool id

        :param center_or_id: 分中心对象或id
        :return:
             QuerySet   # success
        :raise ComputeError
        """
        pools = self.get_pool_queryset_by_center(center_or_id)
        return list(pools.values_list('id', flat=True).all())

    @staticmethod
    def get_stat_center_queryset(filters: dict = None):
        """
        分中心资源统计查询集

        :param filters: center的过滤条件
        :return:
            QuerySet   # success
        """
        qs = Center.objects.all()
        if filters:
            qs = qs.filter(**filters).all()
        return qs.annotate(
            mem_total=DefaultSum('group_set__hosts_set__mem_total'),
            mem_allocated=DefaultSum('group_set__hosts_set__mem_allocated'),
            mem_reserved=DefaultSum('group_set__hosts_set__mem_reserved'),
            real_cpu=DefaultSum('group_set__hosts_set__real_cpu'),
            vcpu_total=DefaultSum('group_set__hosts_set__vcpu_total'),
            vcpu_allocated=DefaultSum('group_set__hosts_set__vcpu_allocated'),
            vm_created=DefaultSum('group_set__hosts_set__vm_created')).all()


class GroupManager:
    """
    宿主机组管理器
    """
    def __init__(self):
        # 机组对象缓存，机组对象数据有变化，需要清除缓存或设置覆盖缓存
        self._cache_groups = {}

    def _cache_group_remove(self, group_id=None):
        """
        尝试从机组对象缓存移除指定的机组对象，未指定group_id，清除所有缓存

        :param group_id: 机组id
        """
        if group_id is None:
            self._cache_groups.clear()
        self._cache_groups.pop(group_id, None)

    def _cache_group_add(self, group):
        """
        缓存一个机组对象

        :param group: 机组对象
        """
        if not isinstance(group, Group):
            return

        gid = group.id
        if gid:
            self._cache_groups[gid] = group

    def _cache_group_get(self, group_id):
        """
        尝试从机组对象缓存获取机组对象

        :return:
            Group() or None
        """
        g = self._cache_groups.get(group_id, None)
        if g and isinstance(g, Group):
            return g
        return None

    @staticmethod
    def get_group_queryset():
        return Group.objects.all()

    @staticmethod
    def get_group_by_id(group_id: int):
        """
        通过id获取宿主机组

        :param group_id: 宿主机组id
        :return:
            Group() # success
            None    #不存在
        :raise ComputeError
        """
        if not isinstance(group_id, int) or group_id < 0:
            raise ComputeError(msg='宿主机组ID参数有误')

        try:
            return Group.objects.filter(id=group_id).first()
        except Exception as e:
            raise ComputeError(msg=f'查询宿主机组时错误,{str(e)}')

    def enforce_group_obj(self, group_or_id):
        """
        转换为机组对象

        :param group_or_id: Group() or id
        :return:
            Group()

        :raise: ComputeError    # 机组不存在，或参数有误
        """
        if isinstance(group_or_id, Group):
            return group_or_id

        if isinstance(group_or_id, int):
            if group_or_id <= 0:
                raise ComputeError(msg='无效的group id')

            group = self._cache_group_get(group_or_id)  # 是否有缓存
            if group:
                return group

            group = self.get_group_by_id(group_or_id)
            if group:
                self._cache_group_add(group)
                return group
            else:
                raise ComputeError(msg='机组不存在')

        raise ComputeError(msg='无效的group or id')

    def get_enable_host_queryset_by_group(self, group_or_id):
        """
        通过宿主机组对象和id获取可用宿主机查询集

        :param group_or_id: 宿主机组对象和id
        :return:
            QuerySet   # success
        :raise ComputeError
        """
        qs = self.get_all_host_queryset_by_group(group_or_id)
        return qs.filter(enable=True)

    def get_all_host_queryset_by_group(self, group_or_id):
        """
        通过宿主机组对象和id获取所有宿主机查询集

        :param group_or_id: 宿主机组对象和id
        :return:
            QuerySet   # success
        :raise ComputeError
        """
        group = self.enforce_group_obj(group_or_id)
        return group.hosts_set.all()

    def get_enable_host_ids_by_group(self,  group_or_id):
        """
        通过宿主机组对象和id获取宿主机id list

        :param group_or_id: 宿主机组对象和id
        :return:
            ids: list   # success
        :raise ComputeError
        """
        hosts = self.get_enable_host_queryset_by_group(group_or_id)

        try:
            ids = list(hosts.values_list('id', flat=True).all())
        except Exception as e:
            raise ComputeError(msg=f'查询宿主机id错误，{str(e)}')
        return ids

    def get_all_host_ids_by_group(self,  group_or_id):
        """
        通过宿主机组对象和id获取所有（包括未激活的）宿主机id list

        :param group_or_id: 宿主机组对象和id
        :return:
            ids: list   # success
        :raise ComputeError
        """
        hosts = self.get_all_host_queryset_by_group(group_or_id)

        try:
            ids = list(hosts.values_list('id', flat=True).all())
        except Exception as e:
            raise ComputeError(msg=f'查询宿主机id错误，{str(e)}')
        return ids

    @staticmethod
    def get_host_queryset_by_group_ids(ids: list):
        """
        通过宿主机组id list获取宿主机查询集

        :param ids: 宿主机组id list
        :return:
            QuerySet   # success
        """
        return Host.objects.filter(group__in=ids).all()

    def get_host_ids_by_group_ids(self, ids: list):
        """
        通过宿主机组id list获取宿主机id list

        :param ids: 宿主机组id list
        :return:
            ids: list   # success
        :raise ComputeError
        """
        hosts = self.get_host_queryset_by_group_ids(ids)
        try:
            ids = list(hosts.values_list('id', flat=True).all())
        except Exception as e:
            raise ComputeError(msg=f'查询宿主机id错误，{str(e)}')
        return ids

    def get_host_ids_by_group_or_ids(self, group_or_ids):
        """
        通过宿主机组对象或id,或id list获取宿主机id list

        :param group_or_ids: 机组对象，机组id,或机组id list
        :return:
            ids: list   # success
        :raise ComputeError
        """
        if isinstance(group_or_ids, list):
            return self.get_host_ids_by_group_ids(group_or_ids)
        elif isinstance(group_or_ids, int) or isinstance(group_or_ids, Group):
            return self.get_all_host_ids_by_group(group_or_ids)

        raise ComputeError(msg='无效的宿主机组参数')

    def get_user_host_queryset(self, user):
        """
        获取用户有权限访问的宿主机查询集

        :param user: 用户对象
        :return:
            QuerySet   # success

        :raise ComputeError
        """
        g_ids = CenterManager().get_user_group_ids(user=user)
        return self.get_host_queryset_by_group_ids(ids=g_ids)

    def get_user_host_ids(self, user):
        """
        获取用户有权限访问的宿主机id list

        :param user: 用户对象
        :return:
            ids: list   # success

        :raise ComputeError
        """
        hosts = self.get_user_host_queryset(user=user)
        try:
            ids = list(hosts.values_list('id', flat=True).all())
        except Exception as e:
            raise ComputeError(msg=f'查询宿主机id错误，{str(e)}')
        return ids

    @staticmethod
    def get_stat_group_queryset(filters: dict = None):
        """
        资源统计宿主机组查询集

        :param filters: group的过滤条件
        :return:
            QuerySet()
        """
        qs = Group.objects.all()
        if filters:
            qs = qs.filter(**filters).all()

        return qs.select_related('center').annotate(
            mem_total=DefaultSum('hosts_set__mem_total'), mem_allocated=DefaultSum('hosts_set__mem_allocated'),
            vcpu_total=DefaultSum('hosts_set__vcpu_total'), vcpu_allocated=DefaultSum('hosts_set__vcpu_allocated'),
            real_cpu=DefaultSum('hosts_set__real_cpu'),
            mem_reserved=DefaultSum('hosts_set__mem_reserved'), vm_created=DefaultSum('hosts_set__vm_created')).all()


class HostManager:
    """
    宿主机管理器
    """
    @staticmethod
    def get_host_by_id(host_id: int):
        """
        通过id获取宿主机元数据模型对象

        :param host_id: 宿主机id
        :return:
            Host() # success
            None    #不存在
        :raise ComputeError
        """
        if not isinstance(host_id, int) or host_id < 0:
            raise ComputeError(msg='宿主机ID参数有误')

        try:
            return Host.objects.select_related('group').filter(id=host_id).first()
        except Exception as e:
            raise ComputeError(msg=f'查询宿主机时错误,{str(e)}')

    def enforce_host_obj(self, host_or_id):
        """
        转换为宿主机对象

        :param host_or_id: Host() or id
        :return:
            Host()

        :raise: ComputeError    # 不存在，或参数有误
        """
        if isinstance(host_or_id, Host):
            return host_or_id

        if isinstance(host_or_id, int):
            if host_or_id <= 0:
                raise ComputeError(msg='无效的host id')

            h = self.get_host_by_id(host_or_id)
            if h:
                return h
            else:
                raise ComputeError(msg='宿主机不存在')

        raise ComputeError(msg='无效的host or id')

    @staticmethod
    def get_hosts_by_group_id(group_id: int):
        """
        获取宿主机组的所有宿主机元数据模型对象

        :param group_id: 宿主机组id
        :return:
            [Host(),]    # success
            raise ComputeError #发生错误

        :raise ComputeError
        """
        if not isinstance(group_id, int) or group_id < 0:
            raise ComputeError(msg='宿主机组ID参数有误')
        try:
            hosts_qs = Host.objects.filter(group=group_id).all()
            return list(hosts_qs)
        except Exception as e:
            raise ComputeError(msg=f'查询宿主机组的宿主机列表时错误,{str(e)}')

    @staticmethod
    def filter_hosts_queryset(group_id: int = 0, enable: bool = True):
        """
        过滤宿主机查询集

        :param group_id: 宿主机组id，默认为0，忽略此参数
        :param enable: True,过滤有效的宿主机；False，不过滤
        :return:
            QuerySet    # success

        :raises: ComputeError
        """
        if group_id < 0:
            raise ComputeError(msg='group_id无效')

        qs = None
        if group_id > 0:
            qs = Host.objects.filter(group=group_id).all()

        if qs is None:
            qs = Host.objects.all()

        if enable:
            qs = qs.filter(enable=True).all()

        return qs

    def get_hosts_list_by_group(self, group_or_id):
        """
        获取宿指定主机组，并且包含指定vlan的所有宿主机元数据模型对象

        :param group_or_id: 宿主机组对象Group()或id
        :return:
            [Host(),]    # success
            raise ComputeError #发生错误

        :raise ComputeError
        """
        if isinstance(group_or_id, int):
            group_id = group_or_id
        else:
            group_id = group_or_id.id

        hosts_qs = self.get_hosts_by_group_id(group_id=group_id)
        try:
            return list(hosts_qs)
        except Exception as e:
            raise ComputeError(msg=f'查询宿主机组的宿主机列表时错误,{str(e)}')

    @staticmethod
    def claim_from_host(host_id: int, vcpu: int, mem: int):
        """
        向宿主机申请资源

        :param host_id: 宿主机id
        :param vcpu: 要申请的cpu数
        :param mem: 要申请的内存大小
        :return:
            Host()  # success
            None    #宿主机不存在
        :raise ComputeError
        """
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

    @staticmethod
    def free_to_host(host_id: int, vcpu: int, mem: int):
        """
        释放从宿主机申请的资源

        :param host_id: 宿主机id
        :param vcpu: 要申请的cpu数
        :param mem: 要申请的内存大小
        :return:
            True    # success
            False   # failed
        """
        # 释放资源
        try:
            host = Host.objects.filter(id=host_id).first()
            if not host:
                return False

            return host.free(vcpu=vcpu, mem=mem)
        except Exception:
            return False

    def filter_meet_requirements(self, hosts: list, vcpu: int, mem: int, claim=False):
        """
        筛选满足申请资源要求的宿主机

        :param hosts: 宿主机列表
        :param vcpu: 要申请的cpu数
        :param mem: 要申请的内存大小
        :param claim: True:立即申请资源
        :return:
            Host()  # success
            None    # 没有足够的资源的宿主机

        :raise ComputeError
        """
        # 检查参数
        if not isinstance(hosts, list):
            raise ComputeError(msg='参数有误，请输入宿主机列表')

        if len(hosts) == 0:  # 没有满足条件的宿主机
            return None

        if not isinstance(hosts[0], Host):
            raise ComputeError(msg='参数有误，请输入宿主机列表')

        if not isinstance(vcpu, int) or vcpu <= 0:
            raise ComputeError(msg='参数有误，vcpu必须是一个正整数')

        if not isinstance(mem, int) or mem <= 0:
            raise ComputeError(msg='参数有误，mem必须是一个正整数')

        random.shuffle(hosts)   # 随机打乱
        for host in hosts:
            # 宿主机是否满足资源需求
            if not host.meet_needs(vcpu=vcpu, mem=mem):
                continue

            if not claim:    # 立即申请资源
                continue

            host = self.claim_from_host(host_id=host.id, vcpu=vcpu, mem=mem)
            if host:
                return host

        return None
