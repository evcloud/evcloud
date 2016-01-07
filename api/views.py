#coding=utf-8

######################################
#@author: bobfu
#@email:  fubo@cnic.cn
#@date:   2015-10-16
#@desc:  api v1.0 视图函数。
#        接受api请求，调用相关api函数进行处理，并转换返回格式。
#        此处不做任何逻辑处理，仅从请求包中获取参数，传入api函数，并将返回值格式化并返回。
######################################

from django.http import HttpResponseRedirect, HttpResponse
import json
from .tools import get_args_from_get, get_args_from_post
from .center import get_list as api_center_get_list
from .group import get_list as api_group_get_list, get as api_group_get
from .ceph import get_list as api_ceph_get_list
from .host import get_list as api_host_get_list, get as api_host_get
from .images import get as api_image_get, get_list as api_image_get_list
from .vm import get as api_vm_get 
from .vm import get_list as api_vm_get_list 
from .vm import create as  api_vm_create
from .vm import status as api_vm_status 
from .vm import op as api_vm_op 
from .vm import edit as api_vm_edit
from .vnc import open as api_vnc_open, close as api_vnc_close
from .auth import  login as api_auth_login, logout as api_auth_logout
from .net import get_vlan as api_net_get_vlan, get_vlan_list as api_net_get_vlan_list

from django.views.decorators.csrf import csrf_exempt

from .tools import login_required

@csrf_exempt
def auth_login(req):
    args = get_args_from_post(req)
    args['ip'] = req.META['REMOTE_ADDR']
    dic = api_auth_login(args)
    return HttpResponse(json.dumps(dic))

@csrf_exempt
def auth_logout(req):
    args = get_args_from_post(req)
    dic = api_auth_logout(args)
    return HttpResponse(json.dumps(dic))

@csrf_exempt
@login_required
def center_get_list(req):
    args = get_args_from_post(req)
    dic = api_center_get_list(args)
#     print dic
    return HttpResponse(json.dumps(dic))

@csrf_exempt
@login_required
def group_get(req): 
    args = get_args_from_post(req)
    dic = api_group_get(args)
    return HttpResponse(json.dumps(dic))

@csrf_exempt
@login_required
def group_get_list(req):
    args = get_args_from_post(req)
#     print args,111111111111
    dic = api_group_get_list(args)
    return HttpResponse(json.dumps(dic))

@csrf_exempt
@login_required
def ceph_get_list(req):
    args = get_args_from_post(req)
    dic = api_ceph_get_list(args)
    return HttpResponse(json.dumps(dic))

@csrf_exempt
@login_required
def host_get(req):
    args = get_args_from_post(req)
    dic = api_host_get(args)
    return HttpResponse(json.dumps(dic))

@csrf_exempt
@login_required
def host_get_list(req):
    args = get_args_from_post(req)
    dic = api_host_get_list(args)
    return HttpResponse(json.dumps(dic))

@csrf_exempt
@login_required
def image_get(req):
    args = get_args_from_post(req)
    dic = api_image_get(args)
    return HttpResponse(json.dumps(dic))

@csrf_exempt
@login_required
def image_get_list(req):
    args = get_args_from_post(req)
    dic = api_image_get_list(args)
    return HttpResponse(json.dumps(dic))

@csrf_exempt
@login_required
def vm_get(req):
    args = get_args_from_post(req)
    dic = api_vm_get(args)
    return HttpResponse(json.dumps(dic))

@csrf_exempt
@login_required
def vm_get_list(req):
    args = get_args_from_post(req)
    dic = api_vm_get_list(args)
    return HttpResponse(json.dumps(dic))

@csrf_exempt
@login_required
def vm_create(req):
    args = get_args_from_post(req)
    args['creator'] = req.user.username
    dic = api_vm_create(args)
    return HttpResponse(json.dumps(dic))

@csrf_exempt
@login_required
def vm_status(req):
    args = get_args_from_post(req)
    dic = api_vm_status(args)
    return HttpResponse(json.dumps(dic))

@csrf_exempt
@login_required
def vm_op(req):
    args = get_args_from_post(req)
    dic = api_vm_op(args)
    return HttpResponse(json.dumps(dic))

@csrf_exempt
@login_required
def vm_edit(req):
    args = get_args_from_post(req)
    dic = api_vm_edit(args)
    return HttpResponse(json.dumps(dic))

@csrf_exempt
@login_required
def vnc_open(req):
    args = get_args_from_post(req)
    dic = api_vnc_open(args)
    return HttpResponse(json.dumps(dic))

@csrf_exempt
@login_required
def vnc_close(req):
    args = get_args_from_post(req)
    dic = api_vnc_close(args)
    return HttpResponse(json.dumps(dic))

@csrf_exempt
@login_required
def net_get_vlan(req):
    args = get_args_from_post(req)
    dic = api_net_get_vlan(args)
    return HttpResponse(json.dumps(dic))

@csrf_exempt
@login_required
def net_get_vlan_list(req):
    args = get_args_from_post(req)
    dic = api_net_get_vlan_list(args)
    return HttpResponse(json.dumps(dic))