from django.shortcuts import render
from django.views.generic.base import View
from django.contrib.auth import get_user_model

from .manager import VmManager, VmError
from compute.managers import CenterManager, HostManager, GroupManager, ComputeError
from network.managers import VlanManager
from vdisk.manager import VdiskManager, VdiskError
from utils.paginators import NumsPaginator

# Create your views here.
User = get_user_model()

def str_to_int_or_default(val, default):
    '''
    字符串转int，转换失败返回设置的默认值

    :param val: 待转化的字符串
    :param default: 转换失败返回的值
    :return:
        int     # success
        default # failed
    '''
    try:
        return int(val)
    except Exception:
        return default

class VmsView(View):
    '''
    虚拟机类视图
    '''
    NUM_PER_PAGE = 20   # Show num per page

    def get(self, request, *args, **kwargs):
        center_id = str_to_int_or_default(request.GET.get('center', 0), 0)
        group_id = str_to_int_or_default(request.GET.get('group', 0), 0)
        host_id = str_to_int_or_default(request.GET.get('host', 0), 0)
        user_id = str_to_int_or_default(request.GET.get('user', 0), 0)
        search = request.GET.get('search', '')

        # 超级用户可以有用户下拉框选项
        auth = request.user
        if auth.is_superuser:
            users = User.objects.all()
        else:   # 普通用户只能查看自己的虚拟机，无用户下拉框选项
            users = None
            user_id = auth.id

        v_manager = VmManager()
        try:
            queryset = v_manager.filter_vms_queryset(center_id=center_id, group_id=group_id, host_id=host_id,
                                                    search=search, user_id=user_id, all_no_filters=auth.is_superuser)
        except VmError as e:
            return render(request, 'error.html', {'errors': ['查询虚拟机时错误',str(e)]})

        try:
            c_manager = CenterManager()
            centers = c_manager.get_center_queryset()
            if center_id > 0:
                groups = c_manager.get_group_queryset_by_center(center_id)
            else:
                groups = None
            if group_id > 0:
                hosts = GroupManager().get_host_queryset_by_group(group_id)
            else:
                hosts = None
        except ComputeError as e:
            return render(request, 'error.html', {'errors': ['查询虚拟机时错误', str(e)]})

        context = {}
        context['center_id'] = center_id if center_id > 0 else None
        context['centers'] = centers
        context['groups'] = groups
        context['group_id'] = group_id if group_id > 0 else None
        context['hosts'] = hosts
        context['host_id'] = host_id if host_id > 0 else None
        context['search'] = search
        context['users'] = users
        context['user_id'] = user_id
        context = self.get_vms_list_context(request, queryset, context)
        return render(request, 'vms_list.html', context=context)

    def get_vms_list_context(self, request, vms_queryset, context:dict):
        # 分页显示
        paginator = NumsPaginator(request, vms_queryset, self.NUM_PER_PAGE)
        page_num = request.GET.get('page', 1)  # 获取页码参数，没有参数默认为1
        vms_page = paginator.get_page(page_num)
        page_nav = paginator.get_page_nav(vms_page)

        context['page_nav'] = page_nav
        context['vms'] = self.vm_list_with_vdisk(vms_page)
        context['count'] = paginator.count
        return context

    def vm_list_with_vdisk(self, vms):
        vms_list = []
        manager = VdiskManager()
        for vm in vms:
            vdisk = manager.get_vm_vdisk_queryset(vm.hex_uuid)
            vm.vdisks = vdisk
            vms_list.append(vm)

        return vms_list


class VmCreateView(View):
    '''创建虚拟机类视图'''
    def get(self, request, *args, **kwargs):
        center_id = str_to_int_or_default(request.GET.get('center_id', 0), 0)

        try:
            c_manager = CenterManager()
            centers = c_manager.get_center_queryset()
            groups = None
            images = None
            if center_id > 0:
                images = c_manager.get_image_queryset_by_center(center_id)
                groups = c_manager.get_user_group_queryset_by_center(center_id, user=request.user)
        except ComputeError as e:
            return render(request, 'error.html', {'errors': ['查询分中心列表时错误', str(e)]})

        context = {}
        context['center_id'] = center_id if center_id > 0 else None
        context['centers'] = centers
        context['groups'] = groups
        context['images'] = images
        context['vlans'] = VlanManager().get_vlan_queryset()
        return render(request, 'vms_create.html', context=context)

