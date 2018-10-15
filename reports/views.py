#coding=utf-8
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect

from django.contrib.auth.decorators import login_required
from .auth import staff_required


from compute.models import Host, Center, Group, Vm
# from .models import Alloc_Host, Alloc_Center, Alloc_Group, Alloc_Host_Latest, Alloc_Center_Latest, Alloc_Group_Latest
# Create your views here.

#from utils.page import get_page
#from utils.views import AbsView
#from utils.route import dispatch_url


@login_required
@staff_required
def index(request):
    return HttpResponseRedirect('/reports/alloclist/')


@login_required
def alloclist(request):   
    dicts={}

    alloc_info = _get_alloc_info(request)
    r_alloc_c1 = alloc_info['r_alloc_center']
    r_alloc_g1 = alloc_info['r_alloc_group']
    r_alloc_h1 = alloc_info['r_alloc_host']
    
    dicts['r_alloc_c'] = r_alloc_c1
    dicts['r_alloc_g'] = r_alloc_g1
    dicts['r_alloc_h'] = r_alloc_h1
    return render(request, 'reports_alloc_list.html',dicts)


@login_required
def alloc_center(request):
    if not request.user.is_superuser:
        dicts={}
        return render_to_response('reports_alloc_center.html', dicts, context_instance=RequestContext(request))

    alloc_info = _get_alloc_info(request)
    r_alloc_c1 = alloc_info['r_alloc_center']
    
    x=[]
    cpu_y={"total":[],"allocated":[],"remainder":[]}
    mem_y={"total":[],"used":[],"remainder":[]}
    
    for i in r_alloc_c1:
       x.append(i['center_name'])
       cpu_y["total"].append(i['vcpu_total'])
       cpu_y["allocated"].append(i['vcpu_allocated'])
       cpu_y["remainder"].append(i['vcpu_total']-i['vcpu_allocated'])
       #转换内存单位MB->GB
       mem_y["total"].append(i['mem_total']/1024)
       mem_y["used"].append(i['mem_used']/1024)
       mem_y["remainder"].append((i['mem_total']-i['mem_used'])/1024)
    
    chart_cpu={"title":"分中心资源分配统计：CPU","xaxis":x,"yaxis":cpu_y,"xtitle":"分中心","ytitle":"cpu(核)"}
    chart_mem={"title":"分中心资源分配统计：内存","xaxis":x,"yaxis":mem_y,"xtitle":"分中心","ytitle":"mem(GB)"}
    dicts={"chart_name":"center","chart_cpu":chart_cpu,"chart_mem":chart_mem,"r_alloc_c":r_alloc_c1}
    return render(request,'reports_alloc_center.html',dicts)


@login_required
def alloc_group(request):
    alloc_info = _get_alloc_info(request)
    r_alloc_g1 = alloc_info['r_alloc_group']

    if not r_alloc_g1:
        dicts={}
        return render_to_response('reports_alloc_group.html', dicts, context_instance=RequestContext(request))
    
    x=[]
    cpu_y={"total":[],"allocated":[],"remainder":[]}
    mem_y={"total":[],"used":[],"remainder":[]}
    for i in r_alloc_g1:
       x.append(i['group_name'])
       cpu_y["total"].append(i['vcpu_total'])
       cpu_y["allocated"].append(i['vcpu_allocated'])
       cpu_y["remainder"].append(i['vcpu_total']-i['vcpu_allocated'])
       #转换内存单位KB->GB
       mem_y["total"].append(i['mem_total']/1024)
       mem_y["used"].append(i['mem_used']/1024)
       mem_y["remainder"].append((i['mem_total']-i['mem_used'])/1024)
    chart_cpu={"title":"主机组资源分配统计：CPU","xaxis":x,"yaxis":cpu_y,"xtitle":"主机组","ytitle":"cpu(核)"}
    chart_mem={"title":"主机组资源分配统计：内存","xaxis":x,"yaxis":mem_y,"xtitle":"主机组","ytitle":"mem(GB)"}
    dicts={"chart_name":"center","chart_cpu":chart_cpu,"chart_mem":chart_mem,"r_alloc_g":r_alloc_g1}
    return render(request,'reports_alloc_group.html',dicts)
    


def _get_alloc_info(request):
    r_alloc_c = []
    r_alloc_g = []
    r_alloc_h = []   

    centers = Center.objects.all()
    for c in centers:
        c_vcpu_total = 0
        c_vcpu_allocated = 0
        c_vcpu_alloc_rate = 0
        c_mem_total = 0
        c_mem_allocated = 0
        c_mem_reserved = 0
        c_mem_alloc_rate = 0
        c_mem_used = 0
        c_mem_used_rate = 0
        c_host_count = 0

        if request.user.is_superuser:
            groups = Group.objects.filter(center_id=c.id)
        else:
            groups = Group.objects.filter(admin_user_id=request.user.id, center_id=c.id)
        for g in groups:            
            g_vcpu_total = 0
            g_vcpu_allocated = 0
            g_vcpu_alloc_rate = 0
            g_mem_total = 0
            g_mem_allocated = 0
            g_mem_reserved = 0
            g_mem_alloc_rate = 0
            g_mem_used = 0
            g_mem_used_rate = 0

            hosts = Host.objects.filter(group_id = g.id)
            for h in hosts:
                vcpu_alloc_rate = 0
                mem_alloc_rate = 0
                h_mem_used = h.mem_allocated + h.mem_reserved
                h_mem_used_rate = 0
                if h.vcpu_total:
                    vcpu_alloc_rate=h.vcpu_allocated / h.vcpu_total
                if h.mem_total:
                    mem_alloc_rate=h.mem_allocated / h.mem_total
                    h_mem_used_rate = h_mem_used / h.mem_total  
                d1 = {"ipv4":h.ipv4,"group_name":g.name,"center_name":c.name,
                      "vcpu_total":h.vcpu_total,"vcpu_allocated":h.vcpu_allocated,"vcpu_alloc_rate":vcpu_alloc_rate,
                      "mem_total":h.mem_total,"mem_allocated":h.mem_allocated,"mem_reserved":h.mem_reserved,"mem_alloc_rate":mem_alloc_rate,
                      "mem_used":h_mem_used,"mem_used_rate":h_mem_used_rate}
                r_alloc_h.append(d1)
                #统计group
                g_vcpu_total += h.vcpu_total
                g_vcpu_allocated += h.vcpu_allocated
                g_mem_total += h.mem_total
                g_mem_allocated += h.mem_allocated
                g_mem_reserved += h.mem_reserved
            #end:for h in hosts
            if g_vcpu_total:
                g_vcpu_alloc_rate = g_vcpu_allocated / g_vcpu_total
            if g_mem_total:
                g_mem_alloc_rate = g_mem_allocated / g_mem_total
                g_mem_used = g_mem_allocated + g_mem_reserved
                g_mem_used_rate = g_mem_used / g_mem_total        
            d1 = {  "group_name":g.name,"center_name":c.name,
                    "vcpu_total":g_vcpu_total,"vcpu_allocated":g_vcpu_allocated,"vcpu_alloc_rate":g_vcpu_alloc_rate,
                    "mem_total":g_mem_total,"mem_allocated":g_mem_allocated,"mem_reserved":g_mem_reserved,
                    "mem_alloc_rate":g_mem_alloc_rate,"host_count":hosts.count(),
                    "mem_used":g_mem_used,"mem_used_rate":g_mem_used_rate}
            r_alloc_g.append(d1)
            #统计center
            c_vcpu_total += g_vcpu_total
            c_vcpu_allocated += g_vcpu_allocated
            c_mem_total += g_mem_total
            c_mem_allocated += g_mem_allocated
            c_mem_reserved += g_mem_reserved
            c_host_count += hosts.count()
        #end: for g in groups
        if c_vcpu_total:
            c_vcpu_alloc_rate = c_vcpu_allocated / c_vcpu_total
        if c_mem_total:
            c_mem_alloc_rate = c_mem_allocated / c_mem_total
            c_mem_used = c_mem_allocated + c_mem_reserved
            c_mem_used_rate = c_mem_used / c_mem_total

        d1 = {  "center_name":c.name,"vcpu_total":c_vcpu_total,"vcpu_allocated":c_vcpu_allocated,"vcpu_alloc_rate":c_vcpu_alloc_rate,
                "mem_total":c_mem_total,"mem_allocated":c_mem_allocated,"mem_reserved":c_mem_reserved,
                "mem_alloc_rate":c_mem_alloc_rate,"host_count":c_host_count,
                "mem_used":c_mem_used,"mem_used_rate":c_mem_used_rate}

        r_alloc_c.append(d1)

    if not request.user.is_superuser:
        r_alloc_c = []

    return {"r_alloc_center":r_alloc_c, "r_alloc_group":r_alloc_g,"r_alloc_host":r_alloc_h}
