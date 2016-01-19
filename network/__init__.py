#coding=utf-8
from .models import Vlan as ModelVlan
from .models import MacIP
from .models import VlanType
from .manager import NetManager
from .vlan import Vlan
from django.contrib.auth.models import User

netmanager = NetManager()
def get_vlans(group_id):
    vlans = netmanager.get_vlan_list_by_group_id(group_id)
    ret_list = []
    for vlan in vlans:
        ret_list.append(Vlan(vlan))
    return ret_list

def get_vlans_by_type(vlan_type_id):
    vlans = netmanager.get_vlan_list_by_type(vlan_type_id)
    ret_list = []
    for vlan in vlans:
        ret_list.append(Vlan(vlan))
    return ret_list
        
def get_vlan(vlan_id):
    vlan = ModelVlan.objects.filter(id = vlan_id)
    if not vlan.exists():
        return False
    return Vlan(vlan[0])

def get_net_info_by_vm(vm_uuid):
    ret_dic = {}
    macip = MacIP.objects.filter(vmid = vm_uuid)
    if macip:
        ret_dic['vlan_id'] = macip[0].vlan.id 
        ret_dic['mac'] = macip[0].mac 
        ret_dic['ipv4'] = macip[0].ipv4 
        ret_dic['vm_uuid'] = macip[0].vmid
        ret_dic['vlan_name'] = macip[0].vlan.vlan
        ret_dic['br'] = macip[0].vlan.br
        ret_dic['vlan_type_code'] = macip[0].vlan.type.code 
        ret_dic['vlan_type_name'] = macip[0].vlan.type.name 
         
        
        return ret_dic
    return False 

def vlan_type_exists(vlan_type_code):
    return netmanager.vlan_type_exists(vlan_type_code)

def vlan_exists(vlan_id, vlan_type_code = None):
    return netmanager.vlan_exists(vlan_id, vlan_type_code)
        
def vlan_filter(vlans, claim=False, vmid=None):
    return netmanager.filter(vlans, claim, vmid)

def mac_claim(mac, vmid):
    return netmanager.claim(mac, vmid)

def mac_release(mac, vmid):
    return netmanager.release(mac, vmid)

def get_vlan_types():
    type_list = VlanType.objects.all().order_by('order')
    ret_list = []
    for t in type_list:
        ret_list.append({
            'code': t.code,
            'name': t.name,
            'order': t.order
            })
    return ret_list