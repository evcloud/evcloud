#coding=utf-8
from filter import HostFilterStrategy as BaseStrategy
from .manager import HostManager

class HostFilterStrategy(BaseStrategy):
    def filter(self, hosts, vcpu, mem):
        hostmanager = HostManager()
        hosts = self._pre_filter(hosts)
        enables = []
        for host in hosts:
            if hostmanager.claim(host, vcpu, mem, 1, True):
                enables.append(host)
            else:
                print hostmanager.error
        
        if len(enables) == 0:
            return None
        max_ram = 0
        best = None
        for host in enables:
            remain = host.mem_total - host.mem_allocated - host.mem_reserved
            if remain > max_ram:
                max_ram = remain
                best = host
        return best