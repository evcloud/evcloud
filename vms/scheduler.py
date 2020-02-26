import random

from network.managers import MacIPManager
from compute.managers import GroupManager, HostManager, ComputeError
from utils.errors import Error


class ScheduleError(Error):
    pass


class HostMacIPScheduler:
    '''
    创建虚拟机宿主机和MAC IP资源分配调度器
    '''
    def schedule(self, vcpu:int, mem:int, group=None, host=None, vlan=None, need_mac_ip=True):
        '''
        申请满足要求的宿主机和mac_ip资源

        group和host必须有一个有效；
        need_mac_ip=True时，vlan不指定自动分配一个可用的mac_ip；

        :param group: 宿主机组 Group()
        :param host: 宿主机 Host()
        :param vcpu: cpu核数
        :param mem: 内存大小MB
        :param vlan: 子网 Vlan(), 默认None不指定子网
        :param need_mac_ip: 是否需要申请MAC IP资源，True(申请)
        :return:
            (host, mac_ip)          # host不为None, mac_ip都可能为None
            raise ScheduleError     # 没有可用的宿主机

        :raises: ScheduleError
        '''
        if host:
            h, mac_ip = self._schedule_by_host_vlan(host=host, vcpu=vcpu, mem=mem, vlan=vlan, need_mac_ip=need_mac_ip)
        elif group:
            h, mac_ip = self._schedule_by_group_vlan(group=group, vcpu=vcpu, mem=mem, vlan=vlan, need_mac_ip=need_mac_ip)
        else:
            raise ScheduleError(msg='必须指定宿主机或宿主机组')

        self.host = h
        self.mac_ip = mac_ip
        return self.host, self.mac_ip

    def _schedule_by_host_vlan(self, host, vcpu: int, mem: int, vlan=None, need_mac_ip=True):
        '''
        通过指定的宿主机host和子网vlan进行宿主机和MAC IP的资源调度

        :param host: 宿主机 Host()
        :param vcpu: cpu核数
        :param mem: 内存大小MB
        :param vlan: 子网 Vlan(), 默认None不指定子网
        :param need_mac_ip: 是否需要申请MAC IP资源，True(申请)
        :return:
            (host, mac_ip)  # mac_ip可能为None

        :raises: ScheduleError
        '''
        if not host:
            raise ScheduleError(msg='host参数无效')

        # 宿主机是否满足资源需求
        if not host.meet_needs(vcpu=vcpu, mem=mem):
            raise ScheduleError(msg='没有足够资源的宿主机可用')

        mac_ip = None
        manager = MacIPManager()
        if need_mac_ip:
            if vlan:
                if host.contains_vlan(vlan):
                    mac_ip = manager.apply_for_free_ip(vlan_id=vlan.id)
                    if not mac_ip:
                        raise ScheduleError(msg=f'指定的子网vlan<{str(vlan)}>内没有可用的mac ip资源')
                else:
                    raise ScheduleError(msg=f'宿主机host<{str(host)}>不在指定的子网vlan<{str(vlan)}>内')
            else:
                vlans = list(host.vlans.all())
                random.shuffle(vlans)   # 打乱顺序
                for v in vlans:
                    mac_ip = manager.apply_for_free_ip(vlan_id=v.id)
                    if mac_ip:
                        self.vlan = v
                        break

            if not mac_ip:
                raise ScheduleError(msg='没有可用的mac ip资源')

        try:
            host = HostManager().claim_from_host(host_id=host.id, vcpu=vcpu, mem=mem)
        except ComputeError as e:
            if mac_ip:
                manager.free_used_ip(ip_id=mac_ip.id)  # 释放已申请的mac ip资源
            raise ScheduleError(msg=str(e))

        return host, mac_ip

    def _schedule_by_group_vlan(self, group, vcpu: int, mem: int, vlan=None, need_mac_ip=True):
        '''
        通过指定的宿主机组group和子网vlan进行宿主机和MAC IP的资源调度

        :param group: 宿主机组 Group()
        :param vcpu: cpu核数
        :param mem: 内存大小MB
        :param vlan: 子网 Vlan(), 默认None不指定子网
        :param need_mac_ip: 是否需要申请MAC IP资源，True(申请)
        :return:
            (host, mac_ip)  #

        :raises: ScheduleError
        '''
        host_list = self._get_host_list(group=group, vlan=vlan)
        if not host_list:
            raise ScheduleError(msg='没有足够资源的宿主机可用')

        host = None
        mac_ip = None
        random.shuffle(host_list)   # 打乱宿主机顺序
        for h in host_list:
            try:
                host, mac_ip = self._schedule_by_host_vlan(host=h, vlan=vlan, vcpu=vcpu, mem=mem, need_mac_ip=need_mac_ip)
            except ScheduleError as e:
                continue

            if not need_mac_ip:
                break
            elif mac_ip:
                break

        if not host:
            if not need_mac_ip:
                msg = '没有足够资源的宿主机可用'
            else:
                msg = '没有足够资源的宿主机或mac ip可用'
            raise ScheduleError(msg=msg)

        return host, mac_ip

    def _get_host_list(self, group, vlan=None):
        '''
        获取指定宿主机组的属于vlan子网的宿主机列表

        :param vlan: 子网对象Vlan()
        :param group_id: 宿主机组Group()，只获取此组的宿主机
        :return:
            list                    # success
            raise ScheduleError     # failed ,未找到宿主机或发生错误

        :raise ScheduleError
        '''
        try:
            if vlan:
                host_list = HostManager().get_hosts_by_group_and_vlan(group_or_id=group, vlan=vlan)
            else:
                host_list = list(GroupManager().get_host_queryset_by_group(group_or_id=group))
        except (ComputeError, Exception) as e:
            raise ScheduleError(msg=f'获取宿主机list错误，{str(e)}')

        return host_list
