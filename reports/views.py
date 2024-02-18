import ipaddress
import json

import math
from django.http import JsonResponse
from django.shortcuts import render, HttpResponse
from django.views import View
from django.db.models import Q

from compute.models import Host
from compute.managers import CenterManager, GroupManager, HostManager
from network.managers import check_ip_in_subnets
from pcservers.models import Room, PcServer
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

        return render(request, 'reports_list.html',
                      context={'centers': centers, 'groups': groups, 'hosts': hosts, 'room': room})


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
    mem_x = mem_all - int(host_mem['HugePages_Free'])
    per = 0
    try:
        if mem_all != 0 and mem_x != 0:
            per = 100 * float(mem_x) / float(mem_all)
    except Exception as e:
        raise e

    mem_p = f'{per:.2f}'  # %
    data = f'{cpu_h}, {cpu_x}, {cpu_y}, {cpu_p}, {mem_all}, {mem_x}, {mem_p}'  # cpu , 虚拟cpu, 内存,
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
        realcpu = request.POST.get('realcpu')
        vcputotal = request.POST.get('vcputotal')
        memtotalint = request.POST.get('memtotalint')

        if not realcpu or not vcputotal or not memtotalint:
            return JsonResponse({'msg_error': f'获取到的值为空，请检查。'}, json_dumps_params={'ensure_ascii': False},
                                status=400)

        realcpu = int(realcpu)
        vcputotal = int(vcputotal)
        memtotalint = int(memtotalint)

        try:
            base_host = HostManager().get_host_by_ipv4(host_ipv4=host_ipv4)
        except Exception as e:
            return JsonResponse({'msg_error': f'{str(e)}'}, json_dumps_params={'ensure_ascii': False}, status=400)

        count = 0
        if realcpu != 0 and base_host.real_cpu != realcpu:
            base_host.pcserver.real_cpu = realcpu
            count += 1

        if vcputotal != 0 and base_host.vcpu_total != vcputotal:
            base_host.vcpu_total = vcputotal
            count += 1

        if memtotalint != 0 and base_host.mem_total != memtotalint:
            base_host.mem_total = memtotalint
            count += 1

        if count == 0:
            return JsonResponse({'msg_error': f'数据为零或新旧数据相同数据不保存。'},
                                json_dumps_params={'ensure_ascii': False},
                                status=400)

        try:
            base_host.pcserver.save()
            base_host.save()
        except Exception as e:
            return JsonResponse({'msg_error': f'无法保存数据， 请重试。 error: {str(e)}'},
                                json_dumps_params={'ensure_ascii': False}, status=400)

        return JsonResponse({'msg': f'数据保存成。'}, json_dumps_params={'ensure_ascii': False})


class ReportsHostBatchDetection(View):

    def get(self, request, *args, **kwargs):
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

        for ip in ip_list:
            try:
                data = get_host_cpu_men_info(host_ipv4=ip)
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
        host_info = json.loads(host_info)

        if not room_id or not group_id or not host_info:
            return JsonResponse({'msg_error': f'未获取到完整数据，请检查。'}, json_dumps_params={'ensure_ascii': False},
                                status=400)

        for key, val in host_info.items():

            try:
                cpu, mem = int(val[0]), int(val[1])
                pc = self.pcserver_check(host_ip=key, cpu=cpu, mem=mem, room_id=int(room_id))
                self.host_check(host_ip=key, cpu=cpu, mem=mem, pcserver_id=pc.id, room_id=int(room_id))
            except Exception as e:
                return JsonResponse({'msg_error': f'保存失败：{str(e)}'}, json_dumps_params={'ensure_ascii': False},
                                    status=400)

        return JsonResponse({'msg': f'保存成功'},
                            json_dumps_params={'ensure_ascii': False})

    def pcserver_check(self, host_ip, cpu, mem, room_id):
        obj = PcServer.objects.filter(host_ipv4=host_ip).first()
        if obj:
            flag = []
            if obj.real_cpu != cpu:
                obj.real_cpu = cpu
                flag.append('real_cpu')

            if obj.real_mem != mem:
                obj.real_mem = mem
                flag.append('real_mem')

            if flag:
                obj.save(update_fields=['real_cpu', 'real_mem'])

            return obj

        obj = PcServer(
            tag_no='x86',
            location='无',
            real_cpu=cpu,
            real_mem=mem,
            host_ipv4=host_ip,
            ipmi_ip=host_ip,
            user='无',
            department_id=room_id
        )
        obj.save()

        return obj

    def host_check(self, host_ip, cpu, mem, pcserver_id, room_id):

        host_obj = Host.objects.filter(pcserver__host_ipv4=host_ip).filter()
        if host_obj:
            if host_obj.vcpu_total != cpu * 4:
                host_obj.vcpu_total = cpu * 4
                host_obj.save(update_fields=['vcpu_total'])
            return host_obj

        host_obj = Host(
            pcserver_id=pcserver_id,
            group_id=room_id,
            vcpu_total=cpu * 4,
            mem_total=mem,
            vm_created=30,
        )
        host_obj.save()

        return host_obj


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
