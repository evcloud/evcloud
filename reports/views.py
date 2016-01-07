#coding=utf-8
import uuid, json, libxml2
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect

from django.contrib.auth.decorators import login_required
from auth import staff_required


from compute.models import Host, Center, Group, Vm
from models import Alloc_Host, Alloc_Center, Alloc_Group, Alloc_Host_Latest, Alloc_Center_Latest, Alloc_Group_Latest
# Create your views here.

#from utils.page import get_page
#from utils.views import AbsView
#from utils.route import dispatch_url


@login_required
@staff_required
def index(request):
    return HttpResponseRedirect('/reports/alloclist/')


def alloclist(request):
    r_alloc_c = _get_alloc_center(request)#.order_by('center_id')
    r_alloc_g = _get_alloc_group(request)
    r_alloc_h = _get_alloc_host(request)
    dicts={}
    r_alloc_c1=[]
    r_alloc_g1=[]
    r_alloc_h1=[]
    if r_alloc_c != None:
        for c in r_alloc_c:
            r = 0
            hostcount = 0
            if c.mem_total != 0:
                r = float(c.mem_allocated+c.mem_reserved)/c.mem_total
                hostcount = _hostcount_center(c.center)
            r_alloc_c1.append({
                           'center_name':c.center_name,'vcpu_total':c.vcpu_total,'vcpu_allocated':c.vcpu_allocated,'vcpu_alloc_rate':c.vcpu_alloc_rate,
                           'mem_total':c.mem_total,'mem_used':c.mem_allocated+c.mem_reserved,'mem_used_rate':r,'hostcount':hostcount})
    if r_alloc_g != None:
        for g in r_alloc_g:
            r = 0
            hostcount =0
            if g.mem_total != 0:
                r = float(g.mem_allocated+g.mem_reserved)/g.mem_total
                hostcount = _hostcount_group(g.group)
            r_alloc_g1.append({
                           'group_name':g.group_name,'center_name':g.center.name,'vcpu_total':g.vcpu_total,'vcpu_allocated':g.vcpu_allocated,'vcpu_alloc_rate':g.vcpu_alloc_rate,
                           'mem_total':g.mem_total,'mem_used':g.mem_allocated+g.mem_reserved,'mem_used_rate':r,'hostcount':hostcount})
    if r_alloc_h != None:
        for h in r_alloc_h:
            r = 0
            if h.mem_total != 0:
                r = float(h.mem_allocated+h.mem_reserved)/h.mem_total
            r_alloc_h1.append({
                           'ipv4':h.ipv4,'group_name':h.group.name,'center_name':h.group.center.name,'vcpu_total':h.vcpu_total,'vcpu_allocated':h.vcpu_allocated,'vcpu_alloc_rate':h.vcpu_alloc_rate,
                           'mem_total':h.mem_total,'mem_used':h.mem_allocated+h.mem_reserved,'mem_used_rate':r})
    dicts['r_alloc_c'] = r_alloc_c1
    dicts['r_alloc_g'] = r_alloc_g1
    dicts['r_alloc_h'] = r_alloc_h1
    #return render(request, 'reports_alloclist.html',dicts)
    return render_to_response('reports_alloc_list.html', dicts, context_instance=RequestContext(request))

def alloc_center(request):
    r_alloc_c = _get_alloc_center(request)
    if r_alloc_c ==None:
        dicts={}
        return render_to_response('reports_alloc_center.html', dicts, context_instance=RequestContext(request))
    x=[]
    cpu_y={"total":[],"allocated":[],"remainder":[]}
    mem_y={"total":[],"used":[],"remainder":[]}
    r_alloc_c1=[]
    for c in r_alloc_c:
        r = 0
        hostcount = 0
        if c.mem_total != 0:
            r = float(c.mem_allocated+c.mem_reserved)/c.mem_total
            hostcount = _hostcount_center(c.center)
        r_alloc_c1.append({
                           'center_name':c.center_name,'vcpu_total':c.vcpu_total,'vcpu_allocated':c.vcpu_allocated,'vcpu_alloc_rate':c.vcpu_alloc_rate,
                           'mem_total':c.mem_total,'mem_used':c.mem_allocated+c.mem_reserved,'mem_used_rate':r,'hostcount':hostcount})
    for i in r_alloc_c1:
       x.append(i['center_name'])
       cpu_y["total"].append(i['vcpu_total'])
       cpu_y["allocated"].append(i['vcpu_allocated'])
       cpu_y["remainder"].append(i['vcpu_total']-i['vcpu_allocated'])
       #转换内存单位MB->GB
       mem_y["total"].append(i['mem_total']/1024)
       mem_y["used"].append(i['mem_used']/1024)
       mem_y["remainder"].append((i['mem_total']-i['mem_used'])/1024)
    
    chart_cpu={"title":u"分中心资源分配统计：CPU","xaxis":x,"yaxis":cpu_y,"xtitle":u"分中心","ytitle":u"cpu(核)"}
    chart_mem={"title":u"分中心资源分配统计：内存","xaxis":x,"yaxis":mem_y,"xtitle":u"分中心","ytitle":u"mem(GB)"}
    dicts={"chart_name":"center","chart_cpu":chart_cpu,"chart_mem":chart_mem,"r_alloc_c":r_alloc_c1}
    #return render(request,'reports_center.html',dicts)
    return render_to_response('reports_alloc_center.html', dicts, context_instance=RequestContext(request))

def alloc_group(request):
    r_alloc_g = _get_alloc_group(request)
    if r_alloc_g ==None:
        dicts={}
        return render_to_response('reports_alloc_group.html', dicts, context_instance=RequestContext(request))
    r_alloc_g1=[]
    for g in r_alloc_g:
        r = 0
        hostcount =0
        if g.mem_total != 0:
            r = float(g.mem_allocated+g.mem_reserved)/g.mem_total
            hostcount = _hostcount_group(g.group)
        r_alloc_g1.append({
                           'group_name':g.group_name,'center_name':g.center.name,'vcpu_total':g.vcpu_total,'vcpu_allocated':g.vcpu_allocated,'vcpu_alloc_rate':g.vcpu_alloc_rate,
                           'mem_total':g.mem_total,'mem_used':g.mem_allocated+g.mem_reserved,'mem_used_rate':r,'hostcount':hostcount})
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
    chart_cpu={"title":u"主机组资源分配统计：CPU","xaxis":x,"yaxis":cpu_y,"xtitle":u"主机组","ytitle":u"cpu(核)"}
    chart_mem={"title":u"主机组资源分配统计：内存","xaxis":x,"yaxis":mem_y,"xtitle":u"主机组","ytitle":u"mem(GB)"}
    dicts={"chart_name":"center","chart_cpu":chart_cpu,"chart_mem":chart_mem,"r_alloc_g":r_alloc_g1}
    #return render(request,'reports_group.html',dicts)
    return render_to_response('reports_alloc_group.html', dicts, context_instance=RequestContext(request))



def _get_alloc_host(request):
    res = None
    if request.user.is_superuser:
        res = Alloc_Host_Latest.objects.order_by('ipv4')
    else:
        res = Alloc_Host_Latest.objects.filter( host__group__admin_user = request.user)
    if res.exists():
        return res
    else:
        return None

def _get_alloc_group(request):
    res = None
    if request.user.is_superuser:
        res = Alloc_Group_Latest.objects.all()#.group_by('center_id')
    else:
        res = Alloc_Group_Latest.objects.filter(group__admin_user = request.user)
    if res.exists():
        return res
    else:
        return None

def _get_alloc_center(request):
    if request.user.is_superuser:
        res = Alloc_Center_Latest.objects.all()#.order_by('center_id')
        if res.exists():
            return res
    return None

def _hostcount_center(center1):
    res = Alloc_Host_Latest.objects.filter(group__center = center1).count()
    if res:
        return res
    return 0


def _hostcount_group(group1):
    res = Alloc_Host_Latest.objects.filter(group = group1).count()
    if res:
        return res
    return 0
