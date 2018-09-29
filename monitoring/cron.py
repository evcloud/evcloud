#coding=utf-8
import logging

from compute.api import CenterAPI,GroupAPI,VmAPI,HostAPI
from compute.vm.vm import VIR_DOMAIN_HOST_DOWN 

from device.api import GPUAPI
from volume.api import VolumeAPI        

from api.error import Error
from api.error import ERROR_CN

from .api import MonitoringAPI

api = MonitoringAPI()
center_api = CenterAPI()
group_api = GroupAPI()
vm_api = VmAPI()
host_api = HostAPI()
gpuapi = GPUAPI()
volumeapi = VolumeAPI()

def run_ha_monitoring():
    """
    虚拟机高可用定时监控
    lzx: 2018-09-25
    """
    global center_api, group_api, vm_api, gpuapi, volumeapi

    group_list = group_api.get_group_list()

    vm_list = []
    vm_dic = {}
    for group in group_list:
        vm_list = vm_api.get_vm_list_by_group_id(group.id,ha_monitored=True)
    for vm in vm_list:
        if vm.host_id in vm_dic:
            vm_dic.append(vm)
        else:
            vm_dic[vm.host_id] = [vm]
    for host_id in vm_dic:
        host = host_api.get_host_by_id(host_id)
        if host_api.host_alive(host.ipv4):
            logging.info("[高可用扫描]宿主机%s:运行中" %(host.ipv4))
            continue

        logging.warning("[高可用扫描]宿主机%s:故障"%(host.ipv4))

        #通过ipmi接口关闭宿主机电源
        if not host_api.host_power_off_by_ipmi(host_id):
            h_log_id = api.create_host_error_log(host_id,host_ipv4,info="故障;无法断电,不执行迁移;")
            continue
        
        host_api.disable_host(host_id) #设置宿主机为不可用状态

        logging.info("[高可用扫描]宿主机%s：执行虚拟机迁移" %host.ipv4)
        
        h_log_id = api.create_host_error_log(host_id,host_ipv4,info="故障;已断电;")
        for vm in vm_dic[host_id]:
            src_host_ipv4 = vm.host_ipv4
            res1 = try_migrate_vm(vm)
            logging.info("[高可用扫描]迁移%s：%s" %(vm.ipv4,str(res1['migrate_res'])))
            vm_log_id = api.create_vm_migrate_log(h_log_id,vm.uuid,
                res1['migrate_res'],src_host_ipv4,res1['dst_host_ipv4'],info=res1['info'])
        
        

def try_migrate_vm(vm):
    '''迁移已经宕机的物理服务器上的高可用虚拟机''' 
    ret = {"migrate_res":False,"info":"","src_host":None}
    if not vm:
        return ret

    try:
        gpu_list = gpuapi.get_gpu_list_by_vm_uuid(vm_uuid)
        if len(gpu_list) > 0:
            ret['info'] = '挂载GPU，无法迁移;'
            return ret

        #只在同一group下寻找可用host,故暂时不考虑挂载磁盘的情况
        host_list = group_api.get_host_list_by_group_id(vm.group_id)

        mem = vm.mem
        vcpu = vm.vcpu
        available_host_list = []
        old_host_ipv4 = vm.host_ipv4 
        dst_host = None
        for host in host_list:
            vlan_id_list = get_vlan_id_list_of_host(host.id)
            if vm.vlan_id not in vlan_id_list: #虚拟机vlan不在host支持的vlan列表中
                continue                         
            if host.enable and not host.exceed_vm_limit() and not host.exceed_mem_limit(mem):
                available_host_list.append(host)
            else:
                continue

        while available_host_list:        
            host = host_api.host_filter(available_host_list, vcpu, mem, claim=False)
            if not host:
                break
            if not host.alive():
                available_host_list.remove(host)
            else:
                dst_host = host
        if not dst_host:
            ret['info'] = "虚拟机迁移：无合适的宿主机；"
        else:
            ret['migrate_res'] = False
            err_msg = ""
            try:                
                 ret['migrate_res'] = vm_api.migrate_vm(vm.uuid, dst_host.id)                   
            except Error as e:
                if e.err in ERROR_CN:
                    err_msg = ERROR_CN[e.err]
            except Exception as e:
                err_msg = str(e)
            finally:
                res_str = "成功" if ret['migrate_res'] else "失败"
                ret['info'] = ret['info'] + \
                            "虚拟机迁移：源宿主机{src_host_ipv4}-新宿主机{dst_host_ipv4},{res_str} {err_msg}；".format(
                                src_host_ipv4=old_host_ipv4,dst_host_ipv4=dst_host.ipv4,res_str=res_str,err_msg=err_msg)
    except Exception as e:
        pass
    return ret






