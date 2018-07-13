#coding=utf-8
from django.conf import settings
from ..models import Host as DBHost
from .host import Host
import subprocess
import importlib

from api.error import Error
from api.error import ERR_HOST_ID
from api.error import ERR_HOST_IPV4
    

class HostManager(object):
    def __init__(self):
        if hasattr(settings, 'HOST_FILTER_STRATEGY'):
            self._set_filter_strategy(settings.HOST_FILTER_STRATEGY)
        else:
            from .filter import HostFilterStrategy
            self.filter_strategy = HostFilterStrategy
        
    def _set_filter_strategy(self, strategy):
        try:
            mo = importlib.import_module(strategy)
            self.filter_strategy = mo.HostFilterStrategy
        except Exception as e:
            raise RuntimeError('set filter strategy error. %s' % e)
            
             
    def list(self, *args, **wargs):
        '''获取宿主机列表'''
        hosts = DBHost.objects.filter(wargs)
        return hosts
    
    def available_hosts(self, group_id):
        hosts = [h for h in DBHost.objects.filter(group_id = group_id, enable=True) 
                 if h.vm_created < h.vm_limit 
                 and h.mem_allocated < h.mem_total - h.mem_reserved]
        return hosts
    
    def filter(self, hosts, vcpu, mem, claim=False):
        '''宿主机筛选'''
        #检查参数
        if type(hosts) != list:
            return False
        for host in hosts:
            if type(host) != Host:
                return False 
        if type(vcpu) != int:
            return False
        if type(mem) != int:
            return False
        
        strategy = self.filter_strategy()
            
        try:
            best_host = strategy.filter(hosts, vcpu, mem)
        except Exception as e:
            if settings.DEBUG: print('host filter error:', e)
            self.error = e
            return False
        else:
            if not best_host:
                if settings.DEBUG: print('host not find')
                self.error = 'Host not find.'
                return False
            
            if claim: 
                res = self.claim(best_host, vcpu, mem)
                if res == True:
                    return best_host
                return False
            return best_host
        return False
    
    def check_host(self, host):
        if type(host) == Host:
            return host
        elif type(host) == DBHost:
            return Host(host)
        else:
            host_obj = None
            try:
                host_obj = DBHost.objects.get(id = host)
            except: pass
            
            if not host_obj:
                try:
                    host_obj = DBHost.objects.get(ipv4 = host)
                except: pass
            
            if not host_obj:
                self.error = 'host error.'
                return False
            return Host(host_obj)
        
    def claim(self, host, vcpu, mem, vm_num = 1, fake=False):
        if settings.DEBUG: print('host manager claim resource: ', host, vcpu, mem, vm_num, fake) 
        host = self.check_host(host)
        if not host:
            return False
        
        res = host.claim(vcpu, mem, vm_num, fake)
        if not res:
            self.error = host.error
            if settings.DEBUG: print(self.error)
            return False
        else:
            return True
            
    def release(self, host, vcpu, mem, vm_num = 1, fake=False):
        if settings.DEBUG: print('释放宿主机资源', host, vcpu, mem, vm_num, fake)
        host = self.check_host(host)
        if not host:
            return False
        
        res = host.release(vcpu, mem, vm_num, fake)
        if not res:
            self.error = host.error 
            return False
        else:
            return True
    
    def host_alive(self, host_ip, times = 1):
        try:
            host = DBHost.objects.get(ipv4 = host_ip)
        except:
            self.error = 'host_ip error.'
            return False
        return Host(host).alive(times)

    def get_host_by_id(self, host_id):
        db = DBHost.objects.filter(id = host_id)
        if not db.exists():
            raise Error(ERR_HOST_ID)
        return Host(db[0])

    def get_host_by_ipv4(self, host_ipv4):
        db = DBHost.objects.filter(ipv4 = host_ipv4)
        if not db.exists():
            raise Error(ERR_HOST_IPV4)
        return Host(db[0])          

    def get_vlan_id_list_of_host(self, host_id):
        host = DBHost.objects.filter(id = host_id)
        if not host.exists():
            raise Error(ERR_HOST_ID)
        return [v.id for v in host[0].vlan.all()]

    def get_host_list_by_group_id(self, group_id):
        hosts = DBHost.objects.filter(group_id = group_id)
        ret_list = []
        for host in hosts:
            ret_list.append(Host(host))
        return ret_list