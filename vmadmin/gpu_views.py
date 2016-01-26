#coding=utf-8
import uuid
import json
import libxml2
import re
from django.shortcuts import render
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.http import HttpResponseRedirect

from django.contrib.auth.decorators import login_required
from .auth import staff_required

from utils.page import get_page
from django.conf import settings

from api.center import get_list as api_center_get_list
from api.host import get_list as api_host_get_list
from api.host import get as api_host_get
from api.images import get_list as api_image_get_list
from api.images import get_type_list as api_image_get_type_list
from api.ceph import get_list as api_ceph_get_list
from api.net import get_vlan_list as api_net_get_vlan_list
from api.net import get_vlan as api_net_get_vlan
from api.net import get_vlan_type_list as api_net_get_vlan_type_list
from api.vnc import open as api_vnc_open
from api.error import ERROR_CN

from .view_tools import get_vm_list_by_center
from .view_tools import vm_list_sort
from .view_tools import image_list_sort
from .view_tools import vlan_list_sort

from api.device import get_gpu_list as api_gpu_get_list
from api.device import set_gpu_remarks as api_gpu_set_remarks
from api.device import get_gpu as api_gpu_get
from api.device import gpu_mount as api_gpu_mount
from api.device import gpu_umount as api_gpu_umount
from api.host import get_list as api_host_get_list
from api.group import get_list as api_group_get_list
from api.vm import get_list as api_vm_get_list
from api.vm import get as api_vm_get

@login_required
def gpu_list_view(req):
    dicts = {}
    group_info = api_group_get_list({'req_user': req.user})
    print(group_info)
    ret_list = []
    if group_info['res']:
        for group in group_info['list']:
            host_info = api_host_get_list({'req_user': req.user, 'group_id': group['id']})
            print(host_info)
            if host_info['res']:
                for host in host_info['list']:
                    gpu_info = api_gpu_get_list({'req_user': req.user, 'host_id': host['id']})
                    if gpu_info['res']:
                        ret_list+=gpu_info['list']
    print(ret_list)
    dicts['p'] = get_page(ret_list, req)
    return render_to_response('vmadmin_gpu_list.html', dicts, context_instance=RequestContext(req))

def _get_gpu_by_id(user, gpu_id):
    gpu_info = api_gpu_get({'req_user': user, 'gpu_id': gpu_id})
    if gpu_info['res']:
        return gpu_info['info']
    return None

def _get_vm_by_id(user, vm_id):
    vm_info = api_vm_get({'req_user': user, 'uuid': vm_id})
    if vm_info['res']:
        return vm_info['info']
    return None

def _get_host_by_id(user, host_id):
    host_info = api_host_get({'req_user': user, 'host_id': host_id})
    if host_info['res']:
        return host_info['info']
    return None

@login_required
def gpu_mount_view(req):
    dicts = {}
    if req.method == "POST":
        gpu_id = req.POST.get('gpu_id', None)
        vm_id = req.POST.get('vm_id', None)
        print(gpu_id, vm_id)
        if gpu_id == None or vm_id == None:
            dicts['error'] = '参数错误'
        else:
            gpu = _get_gpu_by_id(req.user, gpu_id)
            vm = _get_vm_by_id(req.user, vm_id)
            res = api_gpu_mount({'req_user': req.user, 'vm_id':vm_id, 'gpu_id':gpu_id})    
            return HttpResponseRedirect('../detail/?gpu_id=' + gpu_id)            

    gpu_id = req.GET.get('gpu_id', None)
    vm_id = req.GET.get('vm_id', None)
    host_id = req.GET.get('host_id', None)
    gpu = None
    vm = None
    host = None

    if gpu_id != None:
        gpu = _get_gpu_by_id(req.user, gpu_id)
    if vm_id != None:
        vm = _get_vm_by_id(req.user, vm_id)
    if host_id != None:
        host = _get_host_by_id(req.user, host_id)

    if host == None:
        if vm != None:
            host_id_from_vm_or_gpu = vm['host_id']
        elif gpu != None:
            host_id_from_vm_or_gpu = gpu['host_id']
        else:
            host_id_from_vm_or_gpu = None

        if host_id_from_vm_or_gpu:
            host = _get_host_by_id(req.user, host_id_from_vm_or_gpu)

    if host != None:
        gpu_list = []
        gpu_list_info = api_gpu_get_list({'req_user': req.user, 'host_id':host['id']})
        if gpu_list_info['res']:
            gpu_list = gpu_list_info['list']
        
        vm_list = []
        vm_list_info = api_vm_get_list({'req_user': req.user, 'group_id': host['group_id']})
        if vm_list_info['res']:
            for v in vm_list_info['list']:
                if v['host_id'] == host['id']:
                    vm_list.append(v)
        
        dicts['host'] = host
        dicts['vm'] = vm
        dicts['gpu'] = gpu
        dicts['gpu_list'] = gpu_list
        dicts['vm_list'] = vm_list

    
    return render_to_response('vmadmin_gpu_mount.html', dicts, context_instance=RequestContext(req))    

@login_required
def gpu_detail_view(req):
    gpu_id = req.GET.get('gpu_id')
    print(gpu_id)
    res = api_gpu_get({'req_user': req.user, 'gpu_id': gpu_id})
    if not res['res'] and res['err'] in ERROR_CN:
        res['error'] = ERROR_CN[res['err']]
    return render_to_response('vmadmin_gpu_detail.html', res, context_instance=RequestContext(req))

@login_required
def gpu_umount_ajax(req):
    gpu_id = req.POST.get('gpu_id')
    res = api_gpu_umount({'req_user': req.user, 'gpu_id': gpu_id})
    if not res['res'] and res['err'] in ERROR_CN:
        res['error'] = ERROR_CN[res['err']]
    return HttpResponse(json.dumps(res), content_type='application/json')

@login_required
def gpu_edit_remarks_ajax(req):
    remarks = req.POST.get('remarks')
    gpu_id = req.POST.get('gpu_id')
    res = api_gpu_set_remarks({
                       'req_user': req.user,
                       'gpu_id': gpu_id, 
                       'remarks': remarks})
    if not res['res'] and res['err'] in ERROR_CN:
        res['error'] = ERROR_CN[res['err']]
    return HttpResponse(json.dumps(res), content_type='application/json')