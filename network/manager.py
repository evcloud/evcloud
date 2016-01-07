#coding=utf-8
from django.db import transaction
from models import Vlan, MacIP, VlanType
from django.conf import settings

from random import randint

class NetManager(object):
    def filter(self, vlans, claim=False, vmid=None):
        if settings.DEBUG: print '[NetManager.filter]', '开始网络筛选：', vlans, claim, vmid
        if type(vlans) != list:
            return False
        
        available_vlans = []
        for vlan in vlans:
            if type(vlan) != Vlan:
                try:
                    vlan = Vlan.objects.get(pk = vlan)
                except:
                    if settings.DEBUG: print '[NetManager.filter]', '参数vlans错误'
                    return False 
            available_vlans.append(vlan)
            
        vlan = self.vlan_filter(available_vlans, claim, vmid)
            
        if not vlan:
            self.error = 'no IP addresss available.'
            return False
        return vlan
    
    def vlan_filter(self, vlans, claim=False, vmid=None):
        for vlan in vlans:
            if claim and vmid:
                mac = self.claim(vlan, vmid)
                if mac:
                    return vlan
            else:     
                if vlan.macip_set.filter(enable=True, vmid='').exists():
                    return vlan
        return None
    
    error = ''
    def claim(self, vlan, vmid):
        if settings.DEBUG: print 'netmanager claim: ', vlan, vmid
        if type(vlan) != Vlan:
            vlan = Vlan.objects.filter(pk = vlan)
            if not vlan:
                self.error =  'vlan error'
                return None
            vlan = vlan[0]

        mac = MacIP.objects.filter(vlan = vlan, vmid = vmid, enable=True)
        if mac:
            return mac[0].mac
            
        with transaction.atomic():
            mac = MacIP.objects.select_for_update().filter(vlan = vlan, vmid='', enable=True)
            if mac:
                mac = mac[0]
                mac.vmid = vmid
                mac.save()
            else:
                self.error = 'no valid mac'
                return None
        return mac.mac
    
    def claim_mac(self, mac, vmid):
        if settings.DEBUG: print 'netmanager filter claim_mac: ', mac, vmid
        with transaction.atomic():
            if type(mac) == MacIP:
                obj = mac
            else:
                obj = MacIP.objects.select_for_update().filter(mac = mac, vmid='', enable=True)
                if not obj:
                    obj = MacIP.objects.select_for_update().filter(mac = mac, vmid=vmid, enable=True)
            if obj:
                obj = obj[0]
                obj.vmid = vmid
                obj.save()
            else:
                return False
        return True

    def release(self, mac, vmid):
        if settings.DEBUG: print 'release mac:', mac, vmid 
        macipobj = MacIP.objects.filter(mac=mac, vmid=vmid, enable=True)
        for m in macipobj:
            if settings.DEBUG: print 'set null', m.mac
            m.vmid = ''
            m.save()

    def get_mac_by_vmid(self, vmid):
        macip = MacIP.objects.filter(vmid = vmid)
        if macip:
            return macip[0].mac
        return ''

    def get_ipv4_by_vmid(self, vmid):
        macip = MacIP.objects.filter(vmid = vmid)
        if macip:
            return macip[0].ipv4
        return ''

    def get_vlan_by_vmid(self, vmid):
        macip = MacIP.objects.filter(vmid = vmid)
        if macip:
            return macip[0].vlan.vlan
        return ''

    def get_vlanid_by_vmid(self, vmid):
        macip = MacIP.objects.filter(vmid = vmid)
        if macip:
            return macip[0].vlan.id
        return ''

    def get_br_by_vmid(self, vmid):
        macip = MacIP.objects.filter(vmid = vmid)
        if macip:
            return macip[0].vlan.br 
        return  ''

    def get_vlan_list_by_group_id(self, group_id):
        from compute.models import Host as ModelHost
        host_list = ModelHost.objects.filter(group_id = group_id)
        vlan_dic = {}
        for host in host_list:
            for vlan in host.vlan.all():
                if not vlan_dic.has_key(vlan.id):
                    vlan_dic[vlan.id] = vlan
        return vlan_dic.values()
    
    def get_vlan_list_by_type(self, vlan_type):
        if type(vlan_type) != VlanType:
            try:
                vlan_type = VlanType.objects.get(pk = vlan_type)
            except:
                return []
        res = []
        for vlan in vlan_type.vlan_set.filter(enable = True):
            res.append(vlan)
        return res
    
    def vlan_type_exists(self, net_type_id):
        if VlanType.objects.filter(pk = net_type_id).exists():
            return True
        return False
    
    def vlan_exists(self, vlan_id, net_type_id = None):
        if net_type_id != None:
            if Vlan.objects.filter(pk = vlan_id, type_id = net_type_id).exists():
                return True
        else:
            if Vlan.objects.filter(pk = vlan_id).exists():
                return True
        return False
    