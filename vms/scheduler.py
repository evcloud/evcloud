import random

from network.managers import MacIPManager
from compute.managers import GroupManager, HostManager, ComputeError
from utils.errors import Error


class ScheduleError(Error):
    pass


class NoMacIPError(ScheduleError):
    """没有mac ip资源可用"""
    pass


class NoHostError(ScheduleError):
    """没有宿主机资源可用"""
    pass


class NoHostOrMacIPError(ScheduleError):
    """没有宿主机或mac_ip资源可用"""
    pass


class HostMacIPScheduler:
    '''
    创建虚拟机宿主机和MAC IP资源分配调度器
    '''
    def schedule(self, vcpu: int, mem: int, groups: list = [], host=None, vlan=None, need_mac_ip=True, ip_public=None):
        '''
        申请满足要求的宿主机和mac_ip资源

        group和host必须有一个有效；
        need_mac_ip=True时，vlan不指定自动分配一个可用的mac_ip；

        :param groups: 宿主机组列表 [Group()]
        :param host: 宿主机 Host()
        :param vcpu: cpu核数
        :param mem: 内存大小MB
        :param vlan: 子网 Vlan(), 默认None不指定子网
        :param need_mac_ip: 是否需要申请MAC IP资源，True(申请)
        :param ip_public: 指定分配公网或私网ip；默认None（不指定），True(公网)，False(私网)
        :return:
            (host, mac_ip)          # host不为None, mac_ip都可能为None
            raise ScheduleError     # 没有可用的宿主机

        :raises: ScheduleError
        '''
        if host:
            h, mac_ip = self._schedule_by_host_vlan(host=host, vcpu=vcpu, mem=mem, vlan=vlan, need_mac_ip=need_mac_ip, ip_public=ip_public)
        elif not groups:
            raise ScheduleError(msg='无宿主机组资源可用')
        elif len(groups) == 1:
            h, mac_ip = self._schedule_by_group_vlan(group=groups[0], vcpu=vcpu, mem=mem, vlan=vlan, need_mac_ip=need_mac_ip, ip_public=ip_public)
        else:
            h, mac_ip = self._schedule_by_group_list_vlan(groups=groups, vcpu=vcpu, mem=mem, vlan=vlan, need_mac_ip=need_mac_ip, ip_public=ip_public)

        self.host = h
        self.mac_ip = mac_ip
        return self.host, self.mac_ip

    def _schedule_by_host_vlan(self, host, vcpu: int, mem: int, vlan=None, need_mac_ip=True, ip_public=None):
        '''
        通过指定的宿主机host和子网vlan进行宿主机和MAC IP的资源调度

        :param host: 宿主机 Host()
        :param vcpu: cpu核数
        :param mem: 内存大小MB
        :param vlan: 子网 Vlan(), 默认None不指定子网
        :param need_mac_ip: 是否需要申请MAC IP资源，True(申请)
        :param ip_public: 指定分配公网或私网ip；默认None（不指定），True(公网)，False(私网)
        :return:
            (host, mac_ip)  # mac_ip可能为None

        :raises: ScheduleError, NoHostError, NoHostOrMacIPError，NoMacIPError
        '''
        if not host:
            raise NoHostError(msg='host参数无效')

        # 宿主机是否满足资源需求
        if not host.meet_needs(vcpu=vcpu, mem=mem):
            raise NoHostError(msg='没有足够资源的宿主机可用')

        mac_ip = None
        manager = MacIPManager()
        if need_mac_ip:
            mac_ip = self._get_mac_ip(host=host, vlan=vlan, ip_public=ip_public)

        try:
            host = HostManager().claim_from_host(host_id=host.id, vcpu=vcpu, mem=mem)
        except ComputeError as e:
            if mac_ip:
                manager.free_used_ip(ip_id=mac_ip.id)  # 释放已申请的mac ip资源
            raise ScheduleError(msg=str(e))

        return host, mac_ip

    def _get_mac_ip(self, host, vlan, ip_public: bool = None):
        """
        申请mac_ip资源

        :param host: 宿主机对象
        :param vlan: 子网对象， None不指定子网
        :param ip_public: 指定分配公网或私网ip；默认None（不指定），True(公网)，False(私网)
        :return:
            MacIP()
        :raises: NoMacIPError, NoHostOrMacIPError
        """
        manager = MacIPManager()
        mac_ip = None
        if vlan:
            if ip_public:       # 指定分配公网ip
                if not vlan.is_public():
                    raise NoMacIPError(msg='没有可用的公网mac ip资源')
            elif ip_public is not None:     # 指定分配私网ip
                if vlan.is_public():
                    raise NoMacIPError(msg='没有可用的私网mac ip资源')

            if host.contains_vlan(vlan):
                mac_ip = manager.apply_for_free_ip(vlan_id=vlan.id)
                if not mac_ip:
                    raise NoHostOrMacIPError(msg=f'指定的子网vlan<{str(vlan)}>内没有可用的mac ip资源')
            else:
                raise NoHostOrMacIPError(msg=f'宿主机host<{str(host)}>不在指定的子网vlan<{str(vlan)}>内')
        else:
            vlans = list(host.vlans.all())
            random.shuffle(vlans)  # 打乱顺序
            for v in vlans:
                if ip_public:  # 指定分配公网ip
                    if not v.is_public():
                        continue
                elif ip_public is not None:  # 指定分配私网ip
                    if v.is_public():
                        continue

                mac_ip = manager.apply_for_free_ip(vlan_id=v.id)
                if mac_ip:
                    self.vlan = v
                    break

        if not mac_ip:
            if ip_public is None:
                raise NoMacIPError(msg='没有可用的mac ip资源')
            elif ip_public:
                raise NoMacIPError(msg='没有可用的公网mac ip资源')
            else:
                raise NoMacIPError(msg='没有可用的私网mac ip资源')

        return mac_ip

    def _schedule_by_group_vlan(self, group, vcpu: int, mem: int, vlan=None, need_mac_ip=True, ip_public=None):
        '''
        通过指定的宿主机组group和子网vlan进行宿主机和MAC IP的资源调度

        :param group: 宿主机组 Group()
        :param vcpu: cpu核数
        :param mem: 内存大小MB
        :param vlan: 子网 Vlan(), 默认None不指定子网
        :param need_mac_ip: 是否需要申请MAC IP资源，True(申请)
        :param ip_public: 指定分配公网或私网ip；默认None（不指定），True(公网)，False(私网)
        :return:
            (host, mac_ip)  #

        :raises: ScheduleError, NoHostError, NoMacIPError
        '''
        host_list = self._get_host_list(group=group, vlan=vlan)
        if not host_list:
            raise NoHostError(msg='没有足够资源的宿主机可用')

        host = None
        mac_ip = None
        random.shuffle(host_list)   # 打乱宿主机顺序
        err = None
        for h in host_list:
            try:
                host, mac_ip = self._schedule_by_host_vlan(host=h, vlan=vlan, vcpu=vcpu, mem=mem,
                                                           need_mac_ip=need_mac_ip, ip_public=ip_public)
            except ScheduleError as e:
                err = e
                continue

            if not need_mac_ip:
                break
            elif mac_ip:
                break

        if not host:
            if not need_mac_ip:
                raise NoHostError(msg='没有足够资源的宿主机可用')
            elif isinstance(err, NoMacIPError):
                raise err
            else:
                raise NoHostOrMacIPError(msg='没有足够资源的宿主机或mac ip可用')

        return host, mac_ip

    def _schedule_by_group_list_vlan(self, groups, vcpu: int, mem: int, vlan=None, need_mac_ip=True, ip_public=None):
        """
        通过指定的宿主机组group列表和子网vlan进行宿主机和MAC IP的资源调度

        :param groups: 宿主机组列表 [Group()]
        :param vcpu: cpu核数
        :param mem: 内存大小MB
        :param vlan: 子网 Vlan(), 默认None不指定子网
        :param need_mac_ip: 是否需要申请MAC IP资源，True(申请)
        :param ip_public: 指定分配公网或私网ip；默认None（不指定），True(公网)，False(私网)
        :return:
            (host, mac_ip)  #

        :raises: ScheduleError, NoHostOrMacIPError
        """
        random.shuffle(groups)  # 打乱顺序
        for group in groups:
            try:
                return self._schedule_by_group_vlan(group=group, vcpu=vcpu, mem=mem, vlan=vlan,
                                                    need_mac_ip=need_mac_ip, ip_public=ip_public)
            except ScheduleError as e:
                continue

        if ip_public is None:
            msg = '没有足够资源的宿主机或mac ip可用'
        elif ip_public:
            msg = '没有足够资源的宿主机或公网mac ip可用'
        else:
            msg = '没有足够资源的宿主机或私网mac ip可用'

        raise NoHostOrMacIPError(msg=msg)

    def _get_host_list(self, group, vlan=None):
        '''
        获取指定宿主机组的属于vlan子网的宿主机列表

        :param vlan: 子网对象Vlan()
        :param group: 宿主机组Group()，只获取此组的宿主机
        :return:
            list                    # success
            raise ScheduleError     # failed ,未找到宿主机或发生错误

        :raise ScheduleError
        '''
        try:
            if vlan:
                host_list = HostManager().get_hosts_by_group_and_vlan(group_or_id=group, vlan=vlan)
            else:
                host_list = list(GroupManager().get_enable_host_queryset_by_group(group_or_id=group))
        except (ComputeError, Exception) as e:
            raise ScheduleError(msg=f'获取宿主机list错误，{str(e)}')

        return host_list

