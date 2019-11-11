from django.shortcuts import render
from django.views.generic.base import View
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model

from .manager import VmManager, VmError
from compute.managers import CenterManager, HostManager, GroupManager, ComputeError
from network.managers import VlanManager
from vdisk.manager import VdiskManager, VdiskError

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
        paginator = Paginator(vms_queryset, 20)  # Show num vm per page
        page_num = request.GET.get('page', 1)  # 获取页码参数，没有参数默认为1
        vms_page = paginator.get_page(page_num)
        page_nav = self.get_page_nav(request, vms_page, paginator)

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

    def get_page_nav(self, request, vms_page, paginator):
        '''
        页码导航栏相关信息

        :return: dict
            {
                'previous': query_str, # str or None
                'next': query_str,     # str or None
                'page_list': [
                    [page_num:int or str, query_str:str, active:bool],
                ]
            }
        '''
        page_list = []
        current_page = vms_page.number
        if paginator.num_pages >= 2:
            page_list = list(range(max(current_page - 2, 1), min(current_page + 2, paginator.num_pages) + 1))
            # 是否添加'...'
            if (page_list[0] - 1) >= 2:  # '...'在左边
                num = (current_page + 1) // 2
                page_list.insert(0, ('...', num))
            if (paginator.num_pages - page_list[-1]) >= 2:
                num = (current_page + paginator.num_pages) // 2
                page_list.append(('...', num))  # '...'在左边
            # 是否添加第1页
            if page_list[0] != 1:
                page_list.insert(0, 1)
            # 是否添加第最后一页
            if page_list[-1] != paginator.num_pages:
                page_list.append(paginator.num_pages)

        page_nav = {}
        page_nav['page_list'] = self.get_page_list(request, page_list, current_page)

        # 上一页
        if vms_page.has_previous():
            page_nav['previous'] = self.build_page_url_query_str(request, vms_page.previous_page_number())
        else:
            page_nav['previous'] = None
            # 下一页
        if vms_page.has_next():
            page_nav['next'] = self.build_page_url_query_str(request, vms_page.next_page_number())
        else:
            page_nav['next'] = None

        return page_nav

    def get_page_list(self, request, page_nums:list, current_page:int):
        '''
        构建页码导航栏 页码信息

        :param page_nums:
        :param current_page:
        :return:
            [[page_num:int, query_str:str, active:bool], ]
        '''
        page_list = []
        for p in page_nums:
            disp = p    # 页码显示内容
            num = p     # 页码
            if isinstance(p, tuple):
                disp, num = p

            active = False
            query_str = self.build_page_url_query_str(request=request, page_num=num)
            if num == current_page:
                active = True

            page_list.append([disp, query_str, active])

        return page_list

    def build_page_url_query_str(self, request, page_num:int):
        '''
        构建页码对应的url query参数字符串

        :param request:
        :param page_num: 页码
        :return:
            str
        '''
        querys = request.GET.copy()
        querys.setlist('page', [page_num])
        return querys.urlencode()


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

