#coding=utf-8
import json
import ipaddress
from django.shortcuts import render_to_response
from django.shortcuts import render
from django.template import RequestContext
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import StreamingHttpResponse 
from django.contrib.auth.decorators import login_required
from django.conf import settings

from utils.page import get_page

from api.error import ERROR_CN
from api.group import get_list as api_group_get_list
from api.host import get_list as api_host_get_list
from api.monitoring import get_host_err_log_list as api_monitoring_get_host_log_list
from api.monitoring import get_vm_migrate_log_list as api_monitoring_get_vm_log_list


@login_required
def host_err_log_list_view(req):
    dicts = {}
    
    group_info = api_group_get_list({'req_user': req.user})
    host_list = []
    host_log_list = [] 
    host_vm_log_list = [] #[(host_err,[vm_err,vm_err]),(host_err,[vm_err,vm_err]),...]
    
    if group_info['res']:
        for group in group_info['list']:
            host_info = api_host_get_list({'req_user': req.user,'group_id':group['id']})
            if host_info['res']:
                host_list.extend(host_info['list'])

    for host in host_list:
        h_log_info = api_monitoring_get_host_log_list({'req_user': req.user,'host_id':host['id']})
        if h_log_info['res']:
            host_log_list.extend(h_log_info['list'])
    for h_log in host_log_list:
        v_log_info = api_monitoring_get_vm_log_list({'req_user': req.user,'host_error_log_id':h_log['id']})
        v_log_list = []
        if v_log_info['res']:
            v_log_list = v_log_info['list']
            host_vm_log_list.append((h_log,v_log_list))

    dicts['p'] = get_page(host_vm_log_list, req)
    return render(req,'vmadmin_monitoring_host_err_list.html', dicts)
