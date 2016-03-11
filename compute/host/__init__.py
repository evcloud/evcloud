#coding=utf-8

###############################################
# name: 虚拟机管理平台 计算模块  宿主机管理模块
# author: bobfu
# email: fubo@cnic.cn
# time: 2015-10-10
###############################################

# from .filter import HostFilterStrategy

# from .manager import HostManager
# from .host import Host, ModelHost

# hostmanager = HostManager()

# def host_alive(host_ip):
#     '''主机是否能ping通'''
#     return hostmanager.host_alive(host_ip)

# def get_available_hosts(group_id):
#     '''返回有剩余资源且可用（enable字段为True,不判断是否能ping通）的宿主机列表'''
#     return hostmanager.available_hosts(group_id)

# def host_filter(hosts, vcpu, mem, claim=True):
#     '''返回最适合创建新虚拟机的宿主机。claim != True 时不申请资源，仅返回最佳主机。'''
#     return hostmanager.filter(hosts, vcpu, mem, claim)

# #今后将移除此接口函数
# def host_claim(host, vcpu, mem, vm_num = 1):
#     '''从指定宿主机申请资源'''
#     return hostmanager.claim(host, vcpu, mem, vm_num)

# #今后将移除此接口函数
# def host_release(host, vcpu, mem, vm_num = 1):
#     '''从指定宿主机释放资源'''
#     return hostmanager.release(host, vcpu, mem, vm_num)

# def get_host(host):
#     '''将宿主机ID、宿主机IP地址、宿主机model对象转换成VMHost对象。不能转换则返回False'''
#     return hostmanager.check_host(host)

# def get_hosts(group_id):
#     hosts = ModelHost.objects.filter(group_id = group_id)
#     ret_list = []
#     for host in hosts:
#         ret_list.append(Host(host))
#     return ret_list
#     