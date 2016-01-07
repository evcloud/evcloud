#coding=utf-8
from random import randint

class HostFilterStrategy(object):
#     def __init__(self, hosts, vcpu, mem):        
#         self._hosts = hosts
#         self._vcpu = vcpu
#         self._mem = mem
#         self._pre_filter()
#         
#     def _pre_filter(self):
#         hosts = []
#         for host in self._hosts:
#             if host.vm_created < host.vm_limit and host.mem_allocated < host.mem_total - host.mem_reserved:
#                 hosts.append(host)
#         self._hosts = hosts
        
#     def filter(self):
#         if len(self._hosts) > 0:
#             return self._hosts[randint(0, len(self._hosts)-1)]
#         return None

    def _pre_filter(self, hosts_org):
        hosts = []
        for host in hosts_org:
            if host.vm_created < host.vm_limit and host.mem_allocated < host.mem_total - host.mem_reserved:
                hosts.append(host)
        return hosts
        
    def filter(self, hosts, vcpu, mem):
        hosts = self._pre_filter(hosts)
        enables = []
        for host in hosts:
            if host.mem_total - host.mem_reserved - host.mem_allocated >= mem and host.cpu_total - host.cpu_allocated >= vcpu:
                enables.append(host)
        if len(enables) > 0:
            return hosts[randint(0, len(enables)-1)]
        return None