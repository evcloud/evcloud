from django.shortcuts import render
from django.views.generic.base import View
from django.contrib.auth import get_user_model

from vdisk.manager import VdiskManager, VdiskError
from compute.managers import CenterManager, HostManager, GroupManager, ComputeError
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


class VdiskView(View):
    '''
    云硬盘类视图
    '''
    NUM_PER_PAGE = 20  # Show num per page

    def get(self, request, *args, **kwargs):
        center_id = str_to_int_or_default(request.GET.get('center', 0), 0)
        group_id = str_to_int_or_default(request.GET.get('group', 0), 0)
        quota_id = str_to_int_or_default(request.GET.get('quota', 0), 0)
        user_id = str_to_int_or_default(request.GET.get('user', 0), 0)
        search = request.GET.get('search', '')

        # 超级用户可以有用户下拉框选项
        auth = request.user
        if auth.is_superuser:
            users = User.objects.all()
        else:   # 普通用户只能查看自己的虚拟机，无用户下拉框选项
            users = None
            user_id = auth.id

        manager = VdiskManager()
        try:
            queryset = manager.filter_vdisk_queryset(center_id=center_id, group_id=group_id, quota_id=quota_id,
                                                    search=search, user_id=user_id, all_no_filters=auth.is_superuser)
        except VdiskError as e:
            return render(request, 'error.html', {'errors': ['查询云硬盘时错误',str(e)]})

        try:
            c_manager = CenterManager()
            centers = c_manager.get_center_queryset()
            if center_id > 0:
                groups = c_manager.get_group_queryset_by_center(center_id)
            else:
                groups = None
        except ComputeError as e:
            return render(request, 'error.html', {'errors': ['查询机组时错误', str(e)]})

        if group_id > 0:
            quotas = manager.get_quota_queryset_by_group(group_id)
        else:
            quotas = None

        context = {}
        context['center_id'] = center_id if center_id > 0 else None
        context['centers'] = centers
        context['groups'] = groups
        context['group_id'] = group_id if group_id > 0 else None
        context['quotas'] = quotas
        context['quota_id'] = quota_id if quota_id > 0 else None
        context['search'] = search
        context['users'] = users
        context['user_id'] = user_id
        context = self.get_disks_list_context(request, queryset, context)
        return render(request, 'vdisk_list.html', context=context)

    def get_disks_list_context(self, request, queryset, context:dict):
        # 分页显示
        paginator = NumsPaginator(request, queryset, self.NUM_PER_PAGE)
        page_num = request.GET.get('page', 1)  # 获取页码参数，没有参数默认为1
        page = paginator.get_page(page_num)
        page_nav = paginator.get_page_nav(page)

        context['page_nav'] = page_nav
        context['vdisks'] = page
        context['count'] = paginator.count
        return context




