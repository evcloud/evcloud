from django.shortcuts import render
from django.http.response import JsonResponse, HttpResponse

from utils.errors import VmError
from .models import Vlan, MacIP
from .managers import VlanManager


def vlan_list(request):
    if not request.user.is_superuser:
        return HttpResponse('您无权访问此页面')

    vlans = Vlan.objects.all()
    return render(request, 'vlan_list.html', {'vlans': vlans})


def vlan_add(request):
    if not request.user.is_superuser:
        return HttpResponse('您无权访问此页面')

    if request.method == 'GET':
        vlan_id = request.GET.get('vlan')
        vlan = Vlan.objects.get(id=vlan_id)
        return render(request, 'vlan_add.html', {'vlan': vlan})
    elif request.method == 'POST':
        from_ip = request.POST.get('start_ip')
        to_ip = request.POST.get('end_ip')
        vlan_id = request.POST.get('vlan_id')
        write_database = request.POST.get('write_database')
        vlan = VlanManager().get_vlan_by_id(int(vlan_id), user=request.user)

        if write_database == 'false':
            try:
                macips = VlanManager().generate_subips(vlan, from_ip, to_ip)
                return JsonResponse({'ok': True, 'macips': macips})
            except Exception as error:
                return JsonResponse({'ok': False, 'msg': str(error)})
        elif write_database == 'true':
            try:
                macips = VlanManager().generate_subips(vlan, from_ip, to_ip, write_database=True)
                return JsonResponse({'ok': True, 'msg': '导入成功', 'macips': macips})
            except Exception as error:
                return JsonResponse({'ok': False, 'msg': str(error)})
        

def vlan_show(request):
    if not request.user.is_superuser:
        return HttpResponse('您无权访问此页面')

    vlan = request.GET.get('vlan', None)
    vlan_id = request.GET.get('vlan_id', None)
    iptype = request.GET.get('iptype', 'ipv4')
    if vlan:
        macips = MacIP.objects.filter(vlan=vlan)
        macips = macips.prefetch_related('ip_vm')  # 反向预查询（避免多次访问数据库）
        return render(request, 'vlan_show.html', {'macips': macips, 'vlan_id': vlan})
    if vlan_id:
        vlan = VlanManager().get_vlan_by_id(int(vlan_id), user=request.user)
        macips = VlanManager().get_macips_by_vlan(vlan)
        macips = macips.prefetch_related('ip_vm')  # 反向预查询（避免多次访问数据库）
        file_name = None
        config_file = None
        try:
            if iptype == 'ipv4':
                file_name, config_file = VlanManager().generate_config_file(vlan, macips)
            else:
                file_name, config_file = VlanManager().generate_config_file_v6(vlan, macips)
        except Exception as e:
            error = VmError(code=400, msg=str(e))
            return error.render(request=request)

        # 设定文件头，这种设定可以让任意文件都能正确下载，而且已知文本文件不是本地打开
        response = HttpResponse(config_file, content_type='APPLICATION/OCTET-STREAM')
        response['Content-Disposition'] = 'attachment; filename=' + file_name   # 设定传输给客户端的文件名称
        return response  
