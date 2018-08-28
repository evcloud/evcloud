#coding=utf-8
from .vlan import Vlan
from .manager import NetManager
from .models import Vlan as DBVlan
from .models import MacIP
from .models import VlanType

class NetworkAPI(object):
    def __init__(self, manager=None):
        if manager:
            self.manager = manager
        else:
            self.manager = NetManager()

    def get_vlan_list_by_type_id(self, type_id):
        vlans = self.manager.get_vlan_list_by_type(type_id)
        ret_list = []
        for vlan in vlans:
            ret_list.append(Vlan(vlan))
        return ret_list

    def get_vlan_list_by_group_id(self, group_id):
        vlans = self.manager.get_vlan_list_by_group_id(group_id)
        ret_list = []
        for vlan in vlans:
            ret_list.append(Vlan(vlan))
        return ret_list

    def get_vlan_by_id(self, vlan_id):
        vlan = DBVlan.objects.filter(id = vlan_id)
        if not vlan.exists():
            return False
        return Vlan(vlan[0])

    def get_net_info_by_vmuuid(self, vm_uuid):
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

    def vlan_type_exists(self, vlan_type_code):
        return self.manager.vlan_type_exists(vlan_type_code)

    def vlan_exists(self, vlan_id, vlan_type_code = None):
        return self.manager.vlan_exists(vlan_id, vlan_type_code)
        
    def vlan_filter(self, vlans, claim=False, vmid=None):
        return self.manager.filter(vlans, claim, vmid)

    def mac_claim(self, vlan_id, vmid, ipv4=None):
        """ 传入ipv4 则申请指定的ip资源 """
        return self.manager.claim(vlan_id, vmid, ipv4=ipv4)

    def mac_release(self, mac, vmid):
        return self.manager.release(mac, vmid)
    
    def get_vlan_type_list(self):
        type_list = VlanType.objects.all().order_by('order')
        ret_list = []
        for t in type_list:
            ret_list.append({
                'code': t.code,
                'name': t.name,
                'order': t.order
                })
        return ret_list

    def set_vlan_remarks(self, vlan_id,content):
        vlan = DBVlan.objects.filter(id = vlan_id)
        if not vlan.exists():
            return False
        try:
            vlan.update(remarks = content)
        except:
            return False
        return True