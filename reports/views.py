from django.shortcuts import render, HttpResponse
from django.views import View

from compute.models import Host
from compute.managers import CenterManager, GroupManager


class ReportsListView(View):
    '''
    资源统计报表视图
    '''
    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponse('您无权访问此页面')

        centers = CenterManager().get_stat_center_queryset().values('id', 'name', 'mem_total', 'mem_allocated',
                                                                    'vcpu_total', 'vcpu_allocated', 'vm_created')
        groups = GroupManager().get_stat_group_wueryset().values('id', 'name', 'center__name', 'mem_total', 'mem_allocated',
                                                                 'vcpu_total', 'vcpu_allocated', 'vm_created')
        hosts = Host.objects.select_related('group').values('id', 'ipv4', 'group__name', 'mem_total', 'mem_allocated',
                                                                 'vcpu_total', 'vcpu_allocated', 'vm_created').all()
        return render(request, 'reports_list.html', context={'centers': centers, 'groups': groups, 'hosts': hosts})


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
