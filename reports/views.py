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
        groups = GroupManager().get_stat_group_wueryset().values('id', 'name', 'mem_total', 'mem_allocated',
                                                                 'vcpu_total', 'vcpu_allocated', 'vm_created')
        hosts = Host.objects.select_related('group').all()
        return render(request, 'reports_list.html', context={'centers': centers, 'groups': groups, 'hosts': hosts})



