from django.shortcuts import render
from django.views.generic.base import View
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .manager import VmManager, VmError
# Create your views here.

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
        center_id = str_to_int_or_default(request.GET.get('center_id', 0), 0)
        group_id = str_to_int_or_default(request.GET.get('group_id', 0), 0)
        host_id = str_to_int_or_default(request.GET.get('host_id', 0), 0)
        search = request.GET.get('search', '')

        manager = VmManager()
        try:
            queryset = manager.filter_vms_queryset(center_id=center_id, group_id=group_id, host_id=host_id,
                                                    search=search, user_id=request.user.id)
        except VmError as e:
            return render(request, 'error.html', {'errors': ['查询虚拟机时错误',]})

        context = self.get_vms_list_context(request, queryset)
        return render(request, 'vms_list.html', context=context)

    def get_vms_list_context(self, request, vms_queryset):
        context = {}
        # 分页显示
        paginator = Paginator(vms_queryset, 1)  # Show 2 movies per page
        # 页码
        page_list = []
        page_num = request.GET.get('page', 1)  # 获取页码参数，没有参数默认为1
        vms_of_page = paginator.get_page(page_num)
        current_page = vms_of_page.number
        if paginator.num_pages >= 2:
            page_list = list(range(max(current_page - 2, 1), min(current_page + 2, paginator.num_pages) + 1))
            # 是否添加'...'
            if (page_list[0] - 1) >= 2:
                page_list.insert(0, 'left')
                context['left'] = (current_page + 1) // 2
            if (paginator.num_pages - page_list[-1]) >= 2:
                page_list.append('right')
                context['right'] = (current_page + paginator.num_pages) // 2
            # 是否添加第1页
            if page_list[0] != 1:
                page_list.insert(0, 1)
            # 是否添加第最后一页
            if page_list[-1] != paginator.num_pages:
                page_list.append(paginator.num_pages)
        context['page_list'] = page_list
        context['vms'] = vms_of_page
        context['count'] = paginator.count
        return context
