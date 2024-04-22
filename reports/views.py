
import json

from django.http import JsonResponse
from django.shortcuts import render, HttpResponse
from django.views import View
from django.db.models import Q

from compute.models import Host
from compute.managers import CenterManager, GroupManager, HostManager

from pcservers.models import Room
from utils.ev_libvirt.virt import VmDomain



class ReportsListView(View):
    """
    资源统计报表视图
    """

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponse('您无权访问此页面')

        search_center = request.GET.get('center', 0)
        search_group = request.GET.get('group', 0)
        search_host = request.GET.get('host', 0)
        search = request.GET.get('search', 0)

        centers = CenterManager().get_stat_center_queryset().values(
            'id', 'name', 'mem_total', 'mem_allocated', 'real_cpu', 'vcpu_total', 'vcpu_allocated', 'vm_created')

        groups = GroupManager().get_stat_group_queryset().values(
            'id', 'name', 'center__name', 'mem_total', 'mem_allocated',
            'real_cpu', 'vcpu_total', 'vcpu_allocated', 'vm_created')

        hosts = Host.objects.select_related('group').values(
            'id', 'ipv4', 'group__name', 'mem_total', 'mem_allocated',
            'real_cpu', 'vcpu_total', 'vcpu_allocated', 'vm_created').all()

        if search_center:
            hosts = hosts.filter(group__center_id=int(search_center))

        if search_group:
            hosts = hosts.filter(group__id=int(search_group))

        if search_host:
            hosts = hosts.filter(id=int(search_host))

        if search:
            hosts = hosts.filter(Q(ipv4__icontains=search))

        room = Room.objects.all()

        quota = GroupManager().compute_quota(request.user)

        return render(request, 'reports_list.html',
                      context={'centers': centers, 'groups': groups, 'hosts': hosts, 'room': room, 'quota': quota})


def get_host_cpu_men_info(host_ipv4):
    try:
        base_host = HostManager().get_host_by_ipv4(host_ipv4=host_ipv4)
    except Exception as e:
        raise e

    host = VmDomain(host_ip=host_ipv4, vm_uuid='').host
    if not host:
        raise ValueError(f'无效的IP地址, 无法查到宿主机。')

    host_info = host.get_info()  # 获取cpu

    cpu_h = host_info[2]  # 物理cpu
    cpu_x = host_info[2] * 4  # 虚拟cpu  默认 4倍
    cpu_y = base_host.vcpu_allocated  # 已分配
    per = 100 * float(cpu_y) / float(cpu_x)
    cpu_p = f'{per:.2f}'  # %

    host_mem = host.get_hugepages()  # 获取大页内存 dict
    mem_all = int(host_mem['HugePages_Total'])
    mem_x = mem_all - int(host_mem['HugePages_Free'])  # 已使用的大页内存
    per = 0
    try:
        if mem_all != 0 and mem_x != 0:
            per = 100 * float(mem_x) / float(mem_all)
    except Exception as e:
        raise e

    host_virt_men_total = base_host.mem_total
    host_virt_men_allocated = base_host.mem_allocated
    host_virt_per = 0
    try:
        if host_virt_men_total != 0 and host_virt_men_total != 0:
            host_virt_per = 100 * float(host_virt_men_total) / float(host_virt_men_total)
            host_virt_per = f'{host_virt_per:.2f}'
    except Exception as e:
        raise e

    mem_p = f'{per:.2f}'  # %
    data = f'{cpu_h}, {cpu_x}, {cpu_y}, {cpu_p}, {mem_x},{mem_all}, {mem_p}, {host_virt_men_allocated}, {host_virt_men_total}, {host_virt_per}'  # 物理cpu , 虚拟cpu, 已用cpu, cpu 使用率， , 已用大页内存、大页内存、 大页内存使用率、宿主机使用内存， 宿主机总内存
    return data


class ReportHostCpuMem(View):
    """获取宿主机的cpu 内存信息"""

    def get(self, request, *args, **kwargs):
        host_ipv4 = kwargs.get('host_ipv4')
        if not host_ipv4:
            return JsonResponse({'msg_error': f'无效的IP地址。'}, json_dumps_params={'ensure_ascii': False}, status=400)

        try:
            data = get_host_cpu_men_info(host_ipv4=host_ipv4)
        except Exception as e:
            return JsonResponse({'msg_error': f'宿主机查询信息有误， error: {str(e)}。'},
                                json_dumps_params={'ensure_ascii': False}, status=400)

        return JsonResponse({'msg': f'{data}'}, json_dumps_params={'ensure_ascii': False})

    def post(self, request, *args, **kwargs):
        """保存信息"""

        host_ipv4 = kwargs.get('host_ipv4')
        mem_use_num = request.POST.get('mem_use_num')

        mem_total = request.POST.get('mem_total')

        if not mem_use_num or not mem_total:
            return JsonResponse({'msg_error': f'获取到的值为空，请检查。'}, json_dumps_params={'ensure_ascii': False},
                                status=400)

        mem_total = int(mem_total)
        mem_use_num = int(mem_use_num)

        if mem_total == 0 and mem_use_num == 0:
            return JsonResponse({'msg': f'数值为 0 不保存数据。'}, json_dumps_params={'ensure_ascii': False})

        try:
            base_host = HostManager().get_host_by_ipv4(host_ipv4=host_ipv4)
        except Exception as e:
            return JsonResponse({'msg_error': f'{str(e)}'}, json_dumps_params={'ensure_ascii': False}, status=400)

        update_fiedls = []

        if mem_total > 0:
            base_host.mem_total = mem_total
            update_fiedls.append('mem_total')

        if mem_use_num > 0:
            base_host.mem_allocated = mem_use_num
            update_fiedls.append('mem_allocated')

        try:
            # base_host.pcserver.save()
            if update_fiedls:
                base_host.save()
        except Exception as e:
            return JsonResponse({'msg_error': f'无法保存数据， 请重试。 error: {str(e)}'},
                                json_dumps_params={'ensure_ascii': False}, status=400)
        return JsonResponse({'msg': f'数据保存成功。'}, json_dumps_params={'ensure_ascii': False})


class ReportsHostBatchDetection(View):

    """ 一键检测和批量保存"""

    def get(self, request, *args, **kwargs):
        batchdetect_group = request.GET.get('batchdetect_group')
        ip_start = request.GET.get('ip_start')
        ip_end = request.GET.get('ip_end')
        subnet = request.GET.get('ip_subent')  # 子网ip/掩码

        try:
            start = ipaddress.IPv4Address(ip_start)
            end = ipaddress.IPv4Address(ip_end)
        except ipaddress.AddressValueError as e:
            return JsonResponse({'msg_error': f'ipv4地址校验不通过。'},
                                json_dumps_params={'ensure_ascii': False}, status=400)

        try:
            check_ip_in_subnets(subnet_netm=subnet, ip_from=start, ip_to=end)
        except Exception as e:
            return JsonResponse({'msg_error': f'ipv4地址校验不通过。error: {str(e)}'},
                                json_dumps_params={'ensure_ascii': False}, status=400)

        ip_list = [str(ipaddress.IPv4Address(ip)) for ip in range(int(start), int(end) + 1)]

        err_dict = {}
        info_dict = {}

        group = GroupManager().get_group_by_id(group_id=int(batchdetect_group))

        if not group:
            return JsonResponse({'msg_error': f'宿主机组不存在。'},
                                json_dumps_params={'ensure_ascii': False}, status=400)

        sshk_key = group.center.ssh_key

        for ip in ip_list:
            try:
                data = self.get_host_info(ipv4=ip, ssh_key=sshk_key)
            except Exception as e:
                err_dict[ip] = str(e)
                continue
            info_dict[ip] = data

        return JsonResponse({'msg': f'{json.dumps(info_dict)}', 'error': f'{err_dict}'},
                            json_dumps_params={'ensure_ascii': False})

    def post(self, request, *args, **kwargs):
        room_id = request.POST.get('room')
        group_id = request.POST.get('group')
        host_info = request.POST.get('host_info')
        host_info = json.loads(host_info)  # [物理cpu，  大页内存已使用, 大页内存总数]

class ReportsHostBatchDetection(View):
    """ 一键检测 """

    def post(self, request, *args, **kwargs):

        # ip_list = QueryDict(request.body)
        body_string = request.body.decode('utf-8')
        ip_list = json.loads(body_string)
        if not ip_list:
            return

        ip_list_data = {} # {ip:[]}
        for ip in ip_list['ip_list']:

            try:
                data = get_host_cpu_men_info(host_ipv4=ip)
            except Exception as e:
                ip_list_data[ip] = ['未检测', '未检测', '未检测' ]
                continue
                # return JsonResponse({'msg_error': f'宿主机查询信息有误， error: {str(e)}。'},
                #                     json_dumps_params={'ensure_ascii': False}, status=400)
            data = data.split(',')
            ip_list_data[ip] = [data[4], data[5], data[6]]

        return JsonResponse({'msg': f'{ip_list_data}'}, json_dumps_params={'ensure_ascii': False})


class ReportsHostBatchSave(View):
    """批量保存"""
    def post(self, request, *args, **kwargs):
        host_info = json.loads(request.POST.get('host_info'))

        if not host_info:
            return

        for host in host_info:
            if host_info[host][0] == "未检测" or int(host_info[host][0]) == 0:
                continue

            host_obj = Host.objects.filter(pcserver__host_ipv4=host).first()

            if not host_obj:
                continue

            if host_obj.mem_allocated != host_info[host][0]:
                host_obj.mem_allocated = int(host_info[host][0])

            if host_obj.mem_total != host_info[host][1]:
                host_obj.mem_total = int(host_info[host][1])
            try:
                host_obj.save()
            except Exception as e:
                return JsonResponse({'msg': f'保存失败：{str(e)}'}, json_dumps_params={'ensure_ascii': False})

        return JsonResponse({'msg': f'保存成功'}, json_dumps_params={'ensure_ascii': False})



class ReportsCenterView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponse('您无权访问此页面')
        c_id = kwargs.get('id', 0)
        return render(request, 'reports_center.html', context={'center_id': c_id})


class ReportsGroupView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponse('您无权访问此页面')
        g_id = kwargs.get('id', 0)
        return render(request, 'reports_group.html', context={'group_id': g_id})


class QuotaView(View):
    def get(self, request, *args, **kwargs):
        quota = GroupManager().compute_quota(request.user)
        return render(request, 'quota.html', context={'quota': quota})
