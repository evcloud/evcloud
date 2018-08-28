#coding=utf-8
from api.group import get_list as api_group_get_list
from api.vm import get_list as api_vm_get_list

def get_vm_list_by_center(user, center_id):
    '''根据center_id获取虚拟机列表'''
    group_info = api_group_get_list({'req_user': user, 'center_id': center_id})
    vm_list = []
    if group_info['res']:
        for group in group_info['list']:
            vms_info = api_vm_get_list({'req_user': user, 'group_id': group['id']})
            if vms_info['res']:
                vm_list += vms_info['list']
            else:
                print(vms_info)
    return vm_list

def vm_list_sort(vm_list):
    vm_list = sorted(vm_list, key = lambda vm: vm['create_time'], reverse = True)
    return vm_list

def image_list_sort(image_list):
    image_list = sorted(image_list, key = lambda image: image['name'])
    image_list = sorted(image_list, key = lambda image: image['order'])
    return image_list

def vlan_list_sort(vlan_list):
    vlan_list = sorted(vlan_list, key = lambda vlan: vlan['order'])
    return vlan_list