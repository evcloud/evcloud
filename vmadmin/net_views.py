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

from utils.page import get_page
from django.conf import settings

from api.error import ERROR_CN

from api.group import get_list as api_group_get_list
from api.net import get_vlan_list as api_net_get_vlan_list
from api.net import get_vlan as api_net_get_vlan
from api.net import set_vlan_remarks as api_net_set_vlan_remarks
from api.net import get_vlan_ip_list as api_net_get_vlan_ip_list
from api.net import add_vlan_ip as api_net_add_vlan_ip


@login_required
def net_vlan_list_view(req):
    dicts = {}
    group_info = api_group_get_list({'req_user': req.user})
    vlan_list = []
    if group_info['res']:
        for group in group_info['list']:
            vlans_info = api_net_get_vlan_list({'req_user': req.user,'group_id':group['id']})
            if vlans_info['res']:
                vlan_list.extend(vlans_info['list'])
    dicts['p'] = get_page(vlan_list, req)
    return render(req,'vmadmin_net_vlan_list.html', dicts)

@login_required
def net_vlan_ip_list_view(req):
    dicts = {}
    arg_vlan = req.GET.get('vlan')
    #参数校验
    if arg_vlan:
        try:
            arg_vlan = int(arg_vlan)
        except:
            arg_vlan = None
    ip_list = []
    dicts['vlan_info'] = None
    if arg_vlan:
        vlan_info = api_net_get_vlan({'req_user': req.user,'vlan_id':arg_vlan})
        if vlan_info['res']:
            dicts['vlan_info'] = vlan_info['info']
            macips_info = api_net_get_vlan_ip_list({'req_user': req.user,'vlan_id':arg_vlan})   
            if macips_info['res']:
                ip_list = macips_info['list']
    dicts['p'] = get_page(ip_list, req)
    return render(req,'vmadmin_net_vlan_ip_list.html', dicts)

@login_required
def net_vlan_edit_remarks_ajax(req):
    remarks = req.POST.get('remarks')
    vlan_id = req.POST.get('vlan_id')
    res = api_net_set_vlan_remarks({
                       'req_user': req.user,
                       'vlan_id': vlan_id, 
                       'remarks': remarks})
    if not res['res'] and res['err'] in ERROR_CN:
        res['error'] = ERROR_CN[res['err']]
    return HttpResponse(json.dumps(res), content_type='application/json')

@login_required
def net_vlan_conf_file_view(req):
    dicts = {}
    arg_vlan = req.GET.get('vlan')
    #参数校验
    if arg_vlan:
        try:
            arg_vlan = int(arg_vlan)
        except:
            arg_vlan = None
    ip_list = []
    dicts['vlan_info'] = None
    conf_file_str = ""
    if arg_vlan:
        vlan_info = api_net_get_vlan({'req_user': req.user,'vlan_id':arg_vlan})
        if vlan_info['res']:
            dicts['vlan_info'] = vlan_info['info']
            macips_info = api_net_get_vlan_ip_list({'req_user': req.user,'vlan_id':arg_vlan})   
            if macips_info['res']:
                ip_list = macips_info['list']
            conf_file_str = _write_vlan_conf_content(vlan_info['info']['subnetip'],vlan_info['info']['netmask'],ip_list)
    
    the_file_name = "dhcpd.conf"
    if dicts['vlan_info']:
        the_file_name = dicts['vlan_info']['subnetip'] +"_" +the_file_name
    response = StreamingHttpResponse(conf_file_str)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(the_file_name)
    return response


def _write_vlan_conf_content(subnet_ip,netmask,macip_list):
    lines='subnet %s netmask %s {\n'%(subnet_ip,netmask)
    lines=lines+'\t'+'option routers\t10.0.224.254;\n'
    liens=lines+'\t'+'option subnet-mask\t%s;\n'%netmask
    lines=lines+'\t'+'option domain-name-servers\t159.226.12.1;\n'
    lines=lines+'\t'+'option domain-name-servers\t159.226.12.2;\n'
    lines=lines+'\t'+'option time-offset\t-18000; # EAstern Standard Time\n'
    lines=lines+'\t'+'range dynamic-bootp 10.0.224.240 10.0.224.250;\n'
    lines=lines+'\t'+'default-lease-time 21600;\n'
    lines=lines+'\t'+'max-lease-time 43200;\n'
    lines=lines+'\t'+'next-server 159.226.50.246;   #tftp server\n'
    lines=lines+'\t'+'filename "/pxelinux.0";    #boot file\n'
    for ip in macip_list:
        if not ip['ipv4'] or not ip['mac']:
            continue
        ip_fields = ip['ipv4'].split(".")
        if len(ip_fields)<4:
            continue
        host_name = "v_%s_%s" %(ip_fields[2],ip_fields[3])
        line='\t'+'host %s{hardware ethernet %s;fixed-address %s;}\n'%(host_name,ip['mac'],ip['ipv4'])
        lines = lines + line
    lines = lines + "}"
    return lines


@login_required
def net_batch_create_macip(req):
    dicts = {}
    res = True
    err = None

     #获取GET参数
    arg_vlan = req.GET.get('vlan') #vlan_id
    arg_kind = req.GET.get('kind') #生成方式
    arg_subnetip = req.GET.get('subnetip') #子网ip
    arg_netmask = req.GET.get('netmask')
    arg_gateway = req.GET.get('gateway')
    arg_startip = req.GET.get('startip')
    arg_endip = req.GET.get('endip')
    
    #参数校验
    if arg_vlan:
        try:
            arg_vlan = int(arg_vlan)
        except:
            arg_vlan = None

    if arg_kind:
        arg_kind = arg_kind.strip()
    if arg_subnetip:
        arg_subnetip = arg_subnetip.strip() 
    if arg_netmask:
        arg_netmask = arg_netmask.strip()
    if arg_gateway:
        arg_gateway = arg_gateway.strip() 
    if arg_startip:
        arg_startip = arg_startip.strip() 
    if arg_endip:
        arg_endip = arg_endip.strip() 

    dicts['vlan_info'] = None    
    macip_list = []
    if arg_vlan:
        vlan_info = api_net_get_vlan({'req_user': req.user,'vlan_id':arg_vlan})    
    if arg_vlan and vlan_info['res']:
        dicts['vlan_info'] = vlan_info['info']
        if vlan_info['info']['ip_count'] > 0 :
            dicts['err'] = "该VLAN已添加过ip"
        elif not vlan_info['info']['enable']:
            dicts['err'] = "该VLAN未启用"
        else:
            try:
                #根据子网ip和掩码生成ip列表
                if arg_kind == "netmask" and arg_subnetip and arg_netmask: 
                    ip_str = arg_subnetip + "/" +arg_netmask
                    subnetip_obj = ipaddress.IPv4Network(ip_str)
                    for ip1 in subnetip_obj:
                        if str(ip1) == arg_gateway:
                            continue
                        r1,macip = _ip2macip(str(ip1))
                        if r1:
                            macip_list.append(macip)
                    if len(macip_list)>0:
                        macip_list.pop(0)
                    if len(macip_list)>0:
                        macip_list.pop(len(macip_list)-1)
                elif arg_kind == "iprange" and arg_startip and arg_endip :
                    #根据ip范围生成ip列表
                    s_ip = ipaddress.IPv4Address(arg_startip)
                    e_ip = ipaddress.IPv4Address(arg_endip)
                    while e_ip >= s_ip:
                        r1,macip = _ip2macip(str(s_ip))
                        if r1:
                            macip_list.append(macip)
                        s_ip = s_ip + 1
            except Exception as e:
                print(e)
                       
    else:
        dicts['err'] = "无法获取VLAN信息"    
        
    if req.method == "GET":
        dicts['p'] = get_page(macip_list, req)
        return render(req,'vmadmin_net_vlan_ip_batch_create.html', dicts)
    elif req.method == 'POST':#添加入数据库
        success_count = 0
        for i in range(len(macip_list)):
            macip = macip_list[i]
            r2 = api_net_add_vlan_ip({'req_user': req.user,'vlan_id':arg_vlan,
                                'mac':macip['mac'],'ipv4':macip['ipv4'],'enable':True})
        
            if r2['res']:
                macip_list[i]['res'] = True
                success_count += 1
            else:
                macip_list[i]['res'] = False
        fail_count = len(macip_list) - success_count
        dic = {"macip_list":macip_list,"success_count":success_count,"fail_count":fail_count}
        return HttpResponse(json.dumps(dic), content_type='application/json')

def _ip2macip(ip):
    '''
    将主机ip四个号段转成16进制后映射成mac的后8位（16进制位）,
    例如：10.0.80.12对应16进制“0A:00:50:0C”，映射成C8:00:0A:00:50:0C
    '''
    ret_dic = {"ipv4":ip,"mac":'',"hostname":''}
    ip = ip.replace(' ','')    
    ip_fields = ip.split(".")
    dec2hex = ['0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F']
    if len(ip_fields)<4:
        return False,ret_dic
    ret_dic['hostname'] = "v_" + "_".join(ip_fields)
    for i in range(4):
        ip_fields[i] = int(ip_fields[i])
        ip_0 = ip_fields[i] // 16
        ip_1 = ip_fields[i] % 16
        ip_fields[i] = dec2hex[ip_0] + dec2hex[ip_1]
    ret_dic['mac'] = 'C8:00:'+":".join(ip_fields)
    
    return True,ret_dic
