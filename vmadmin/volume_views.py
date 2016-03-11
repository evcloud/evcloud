#coding=utf-8
import json
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.http import HttpResponseRedirect

from django.contrib.auth.decorators import login_required

from utils.page import get_page
from django.conf import settings

from api.error import ERROR_CN
from api.center import get_list as api_center_get_list
from api.group import get_list as api_group_get_list
from api.ceph import get_list as api_ceph_get_list
from api.ceph import get as api_ceph_get
from api.vm import get as api_vm_get
from api.vm import get_list as api_vm_get_list

from api.volume import get_list as api_volume_get_list
from api.volume import create as api_volume_create
from api.volume import delete as api_volume_delete
from api.volume import set_remark as api_volume_set_remark
from api.volume import get as api_volume_get
from api.volume import mount as api_volume_mount
from api.volume import umount as api_volume_umount

@login_required
def volume_list_view(req):
    dicts = {}

    volume_info = api_volume_get_list({'req_user': req.user})
    ret_list= []
    if volume_info['res']:
        ret_list += volume_info['list']
    dicts['p'] = get_page(ret_list, req)
    return render_to_response('vmadmin_volume_list.html', dicts, context_instance=RequestContext(req))

@login_required
def volume_create_view(req):
    dicts = {}

    if req.method == 'POST':
        group_id = req.POST.get('group', None)
        size = req.POST.get('size', None)
        remarks = req.POST.get('remarks', None)
        print(group_id, size, remarks)
        if not group_id or not group_id.isdigit() or not size or not size.isdigit() or float(size) <= 0:
            dicts['alert_msg'] = '参数错误'
        size = int(float(size) * 1024)
        res = api_volume_create({'req_user':req.user, 'group_id': int(group_id), 'size': size})
        if res['res']:
            return HttpResponseRedirect('../list/')
        else:
            if res['err'] in ERROR_CN:
                dicts['alert_msg'] = ERROR_CN[res['err']]
            else:
                dicts['alert_msg'] = res['err']

    center_dic = api_center_get_list({'req_user': req.user})
    if center_dic['res']:
        dicts['center_list'] = center_dic['list']

    center_id = req.GET.get('center', None)
    if not center_id and len(dicts['center_list']) > 0:
        center_id = dicts['center_list'][0]['id']
    if center_id:
        group_list_info = api_group_get_list({'req_user': req.user, 'center_id': center_id})
        group_list = []
        if group_list_info['res']:
            group_list = group_list_info['list']
        dicts['group_list'] = group_list

    return render_to_response('vmadmin_volume_create.html', dicts, context_instance=RequestContext(req))

@login_required
def volume_delete_ajax(req):
    volume_id = req.POST.get('volume_id')
    res = api_volume_delete({'req_user': req.user, 'volume_id': volume_id})
    if not res['res'] and res['err'] in ERROR_CN:
        res['error'] = ERROR_CN[res['err']]
    return HttpResponse(json.dumps(res), content_type='application/json')

@login_required
def volume_edit_remarks_ajax(req):
    remarks = req.POST.get('remarks')
    volume_id = req.POST.get('volume_id')
    res = api_volume_set_remark({
                       'req_user': req.user,
                       'volume_id': volume_id, 
                       'remarks': remarks})
    if not res['res'] and res['err'] in ERROR_CN:
        res['error'] = ERROR_CN[res['err']]
    return HttpResponse(json.dumps(res), content_type='application/json')

def _get_vm_by_id(user, vm_id):
    vm_info = api_vm_get({'req_user': user, 'uuid': vm_id})
    if vm_info['res']:
        return vm_info['info']
    return None

def _get_cephpool_by_id(user, cephpool_id):
    host_info = api_host_get({'req_user': user, 'host_id': host_id})
    if host_info['res']:
        return host_info['info']
    return None

def _get_cephpool_list_by_center_id(user, center_id):
    cephpool_list_info = api_ceph_get_list({'req_user': user, 'center_id': center_id})
    if cephpool_list_info['res']:
        return cephpool_list_info['list']
    return []

def _get_volume_by_id(user, volume_id):
    volume_info = api_volume_get({'req_user': user, 'volume_id': volume_id})
    if volume_info['res']:
        return volume_info['info']
    return None

@login_required
def volume_mount_ceph_view(req):
    dicts = {}
    if req.method == 'POST':
        print(req.POST)
        vm_uuid = req.POST.get('vm_uuid', None)
        volume_id = req.POST.get('volume_id', None)
        volume = _get_volume_by_id(req.user, volume_id)
        if not volume:
            dicts['alert_msg'] = '参数错误'
        else:
            if volume['vm']:
                dicts['alert_msg'] = '云硬盘已挂载'
            else:
                res = api_volume_mount({'req_user': req.user, 'vm_uuid':vm_uuid, 'volume_id':volume_id})
                if res['res']:
                    dicts['alert_msg'] = '挂载成功！'
                elif res['err'] in ERROR_CN:
                    dicts['alert_msg'] = ERROR_CN[res['err']]
                else:
                    dicts['alert_msg'] = '挂载失败'

    volume_id = req.GET.get('volume_id', None)
    vm_id = req.GET.get('vm_id', None)
    volume = None
    vm = None
    
    if volume_id != None:
        volume = _get_volume_by_id(req.user, volume_id)
    if vm_id != None:
        vm = _get_vm_by_id(req.user, vm_id)

    volume_list = []
    vm_list = []
    if vm:
        volume_list_info = api_volume_get_list({'req_user': req.user, 'group_id': vm['group_id']})
        if volume_list_info['res']:
            for vol in volume_list_info['list']:
                if not vol['enable']:
                    continue
                if vol['group_id'] != vm['group_id']:
                    continue
                if vol['vm']:
                    continue
                if req.user.is_superuser or vol['user_name'] == req.user.username:
                    volume_list.append(vol)
        # cephpool_list = _get_cephpool_list_by_center_id(req.user, vm['center_id'])
        # for cephpool in cephpool_list:
        #     volume_list_info = api_volume_get_list({'req_user': req.user, 'cephpool_id': cephpool['id']})
        #     if volume_list_info['res']:
        #         volume_list += volume_list_info['list']
        mounted_volume_list_info = api_volume_get_list({'req_user': req.user, 'vm_uuid':vm['uuid']})
        if mounted_volume_list_info['res']:
            vm['volumes'] = mounted_volume_list_info['list']
    elif volume:
        vm_list_info = api_vm_get_list({'req_user': req.user, 'group_id': volume['group_id']})
        if vm_list_info['res']:
            if req.user.is_superuser:
                vm_list += vm_list_info['list']
            else:
                for vm_info in vm_list_info['list']:
                    if vm_info['creator'] == req.user.username:
                        vm_list.append(vm_info)

        # volume_cephpool_info = api_ceph_get({'req_user': req.user, 'cephpool_id': volume['cephpool_id']})
        # if volume_cephpool_info['res']:
        #     group_list_info = api_group_get_list({'req_user': req.user, 'center_id': volume_cephpool_info['info']['center_id']})
        #     if group_list_info['res']:
        #         for group in group_list_info['list']:
        #             vm_list_info = api_vm_get_list({'req_user': req.user, 'group_id': group['id']})
        #             if vm_list_info['res']:
        #                 if req.user.is_superuser:
        #                     vm_list += vm_list_info['list']
        #                 else:
        #                     for vm_info in vm_list_info['list']:
        #                         if vm_info['creator'] == req.user.username:
        #                             vm_list.append(vm_info)
    
    dicts['volume'] = volume
    dicts['vm'] = vm
    dicts['volume_list'] = volume_list
    dicts['vm_list'] = vm_list

    if volume and volume['enable'] == False:
        dicts['alert_msg'] = '该设备不可用'

    return render_to_response('vmadmin_volume_mount_ceph.html', dicts, context_instance=RequestContext(req))  

@login_required
def volume_umount_ceph_ajax(req):
    volume_id = req.POST.get('volume_id')
    res = api_volume_umount({'req_user': req.user, 'volume_id': volume_id})
    if not res['res'] and res['err'] in ERROR_CN:
        res['error'] = ERROR_CN[res['err']]
    return HttpResponse(json.dumps(res), content_type='application/json')

# def _get_gpu_by_id(user, gpu_id):
#     gpu_info = api_gpu_get({'req_user': user, 'gpu_id': gpu_id})
#     if gpu_info['res']:
#         return gpu_info['info']
#     return None




#  

# @login_required
# def gpu_umount_ajax(req):
#     gpu_id = req.POST.get('gpu_id')
#     res = api_gpu_umount({'req_user': req.user, 'gpu_id': gpu_id})
#     if not res['res'] and res['err'] in ERROR_CN:
#         res['error'] = ERROR_CN[res['err']]
#     return HttpResponse(json.dumps(res), content_type='application/json')

# @login_required
# def gpu_edit_remarks_ajax(req):
#     remarks = req.POST.get('remarks')
#     gpu_id = req.POST.get('gpu_id')
#     res = api_gpu_set_remarks({
#                        'req_user': req.user,
#                        'gpu_id': gpu_id, 
#                        'remarks': remarks})
#     if not res['res'] and res['err'] in ERROR_CN:
#         res['error'] = ERROR_CN[res['err']]
#     return HttpResponse(json.dumps(res), content_type='application/json')