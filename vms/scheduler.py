import random

from network.managers import MacIPManager, VlanManager
from compute.managers import GroupManager, HostManager, ComputeError
from utils import errors


class HostMacIPScheduler:
    """
    创建虚拟机宿主机和MAC IP资源分配调度器
    """
    def schedule(self, vcpu: int, mem: int, groups: list = None, host=None, vlan=None,
                 need_mac_ip=True, ip_public=None):
        """
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
        """
        if host:
            h, mac_ip = self.schedule_by_host_vlan(host=host, vcpu=vcpu, mem=mem, vlan=vlan,
                                                   need_mac_ip=need_mac_ip, ip_public=ip_public)
        elif not groups:
            raise errors.ScheduleError.from_error(errors.NoHostGroupError(msg='无宿主机组资源可用'))
        elif len(groups) == 1:
            h, mac_ip = self.schedule_by_group_vlan(group=groups[0], vcpu=vcpu, mem=mem, vlan=vlan,
                                                    need_mac_ip=need_mac_ip, ip_public=ip_public)
        else:
            h, mac_ip = self.schedule_by_group_list_vlan(groups=groups, vcpu=vcpu, mem=mem, vlan=vlan,
                                                         need_mac_ip=need_mac_ip, ip_public=ip_public)

        self.host = h
        self.mac_ip = mac_ip
        return self.host, self.mac_ip

    def schedule_by_host_vlan(self, host, vcpu: int, mem: int, vlan=None, need_mac_ip=True, ip_public=None):
        """
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
        """
        if not host:
            raise errors.NoHostError(msg='host参数无效')

        if vlan and host.group_id != vlan.group_id:
            exc = errors.AcrossGroupConflictError(
                msg=f'宿主机host<{str(host)}>和指定的子网vlan<{str(vlan)}>不在同一宿主机组内')
            raise errors.ScheduleError.from_error(exc)

        if need_mac_ip:
            ok, vlan_list = self.has_free_mac_ip_in_group(group=host.group_id, ip_public=ip_public)
            if not ok:
                raise errors.NoMacIPError(msg='没有mac ip可用')

        return self.schedule_hosts_vlan(host_list=[host], vcpu=vcpu, mem=mem, vlan=vlan,
                                        need_mac_ip=need_mac_ip, ip_public=ip_public)

    def get_mac_ip(self, vlan_list: list, ip_public: bool = None):
        """
        申请mac_ip资源

        :param vlan_list: 子网对象list
        :param ip_public: 指定分配公网或私网ip；默认None（不指定），True(公网)，False(私网)
        :return:
            MacIP()
        :raises: NoMacIPError, NoHostOrMacIPError
        """
        manager = MacIPManager()
        mac_ip = None

        random.shuffle(vlan_list)  # 打乱顺序
        for v in vlan_list:
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
                raise errors.NoMacIPError(msg='没有可用的mac ip资源')
            elif ip_public:
                raise errors.NoMacIPError(msg='没有可用的公网mac ip资源')
            else:
                raise errors.NoMacIPError(msg='没有可用的私网mac ip资源')

        return mac_ip

    def schedule_by_group_vlan(self, group, vcpu: int, mem: int, vlan=None, need_mac_ip=True, ip_public=None):
        """
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
        """
        if vlan and group.id != vlan.group_id:
            exc = errors.AcrossGroupConflictError(
                msg=f'宿主机组和指定的子网vlan<{str(vlan)}>不在同一宿主机组内')
            raise errors.ScheduleError.from_error(exc)

        host_list = self.get_host_list(group=group)
        if not host_list:
            raise errors.NoHostError(msg='没有足够资源的宿主机可用')

        if need_mac_ip:
            ok, vlan_list = self.has_free_mac_ip_in_group(group=group, ip_public=ip_public)
            if not ok:
                raise errors.NoMacIPError(msg='没有mac ip可用')

        return self.schedule_hosts_vlan(host_list=host_list, vcpu=vcpu, mem=mem, vlan=vlan,
                                        need_mac_ip=need_mac_ip, ip_public=ip_public)

    def schedule_by_group_list_vlan(self, groups, vcpu: int, mem: int, vlan=None, need_mac_ip=True, ip_public=None):
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
                return self.schedule_by_group_vlan(group=group, vcpu=vcpu, mem=mem, vlan=vlan, need_mac_ip=need_mac_ip,
                                                   ip_public=ip_public)
            except errors.ScheduleError as e:
                continue

        if ip_public is None:
            msg = '没有足够资源的宿主机或mac ip可用'
        elif ip_public:
            msg = '没有足够资源的宿主机或公网mac ip可用'
        else:
            msg = '没有足够资源的宿主机或私网mac ip可用'

        raise errors.NoHostOrMacIPError(msg=msg)

    @staticmethod
    def get_host_list(group):
        """
        获取指定宿主机组的宿主机列表

        :param group: 宿主机组Group()，只获取此组的宿主机
        :return:
            list                    # success
            raise ScheduleError     # failed ,未找到宿主机或发生错误

        :raise ScheduleError
        """
        try:
            host_list = list(GroupManager().get_enable_host_queryset_by_group(group_or_id=group))
        except (ComputeError, Exception) as e:
            raise errors.ScheduleError(msg=f'获取宿主机list错误，{str(e)}')

        return host_list

    def schedule_hosts_vlan(self, host_list: list, vcpu: int, mem: int, vlan=None, need_mac_ip=True, ip_public=None):
        """
        通过指定的宿主机list和子网vlan进行宿主机和MAC IP的资源调度

        :param host_list: 宿主机实例列表
        :param vcpu: cpu核数
        :param mem: 内存大小MB
        :param vlan: 子网 Vlan(), 默认None不指定子网
        :param need_mac_ip: 是否需要申请MAC IP资源，True(申请)
        :param ip_public: 指定分配公网或私网ip；默认None（不指定），True(公网)，False(私网)
        :return:
            (host, mac_ip)  # mac_ip=None if need_mac_ip==False

        :raises: ScheduleError, NoHostError, NoMacIPError
        """
        if not host_list:
            raise errors.NoHostError(msg='没有足够资源的宿主机可用')

        host = None
        mac_ip = None
        random.shuffle(host_list)  # 打乱宿主机顺序
        for h in host_list:
            # 宿主机是否满足资源需求
            if not h.meet_needs(vcpu=vcpu, mem=mem):
                continue

            host = h
            break

        if not host:
            raise errors.NoHostError(msg='没有足够资源的宿主机可用')

        if need_mac_ip:
            if vlan:
                vlan_list = [vlan]
            else:
                vlan_list = self.get_vlan_list_by_group(group=host.group_id)

            mac_ip = self.get_mac_ip(vlan_list=vlan_list, ip_public=ip_public)

        try:
            host = HostManager().claim_from_host(host_id=host.id, vcpu=vcpu, mem=mem)
        except ComputeError as e:
            if mac_ip:
                MacIPManager().free_used_ip(ip_id=mac_ip.id)  # 释放已申请的mac ip资源
            raise errors.ScheduleError.from_error(e)

        return host, mac_ip

    def has_free_mac_ip_in_group(self, group, ip_public=None):
        """
        宿主机组是否有可用的mac ip

        :param group: 宿主机组实例或id
        :param ip_public: 指定分配公网或私网ip；默认None（不指定），True(公网)，False(私网)
        :return:    (bool, list)
            True, [Vlan()]
            False, [Vlan()]

        :raises: ScheduleError
        """
        vlans = self.get_vlan_list_by_group(group)
        ok = self.has_free_mac_ip_in_vlan_list(vlan_list=vlans, ip_public=ip_public)
        return ok, vlans

    @staticmethod
    def has_free_mac_ip_in_vlan_list(vlan_list: list, ip_public=None):
        """
        检查是否有可用的mac ip资源

        :param vlan_list: vlan实例列表
        :param ip_public: 指定分配公网或私网ip；默认None（不指定），True(公网)，False(私网)
        :return:
            True
            False

        :raises: ScheduleError
        """
        manager = MacIPManager()
        for v in vlan_list:
            if ip_public:  # 指定分配公网ip
                if not v.is_public():
                    continue
            elif ip_public is not None:  # 指定分配私网ip
                if v.is_public():
                    continue
            try:
                ok = manager.has_free_ip_in_vlan(vlan_id=v.id)
            except Exception as e:
                raise errors.ScheduleError(msg=str(e))

            if ok:
                return True

        return False

    @staticmethod
    def get_vlan_list_by_group(group):
        """
        获取宿主机组的vlan列表

        :param group: 宿主机组实例或id
        :return:
            list

        :raises: ScheduleError
        """
        try:
            vlans = VlanManager().get_group_vlan_queryset(group=group)
            return list(vlans)
        except Exception as e:
            raise errors.ScheduleError(msg=f'查询子网vlan错误，{e}')
