from django.shortcuts import render
from django.views import View
from django.contrib.auth import get_user_model

from compute.managers import CenterManager, ComputeError
from utils.paginators import NumsPaginator
from .managers import ImageManager, ImageError
from .models import Image

User = get_user_model()


def str_to_int_or_default(val, default):
    """
    字符串转int，转换失败返回设置的默认值

    :param val: 待转化的字符串
    :param default: 转换失败返回的值
    :return:
        int     # success
        default # failed
    """
    try:
        return int(val)
    except Exception:
        return default


class ImageView(View):
    """
    镜像列表视图
    """
    NUM_PER_PAGE = 20  # Show num per page

    def get(self, request, *args, **kwargs):
        center_id = str_to_int_or_default(request.GET.get('center', 0), 0)
        tag = str_to_int_or_default(request.GET.get('tag', 0), 0)
        sys_type = str_to_int_or_default(request.GET.get('sys_type', 0), 0)
        search = request.GET.get('search', '')

        try:
            api = ImageManager()
            queryset = api.filter_image_queryset(center_id=center_id, tag=tag, sys_type=sys_type, search=search,
                                                 all_no_filters=True)
        except ImageError as e:
            return render(request, 'error.html', {'errors': ['查询镜像时错误', str(e)]})

        try:
            centers = CenterManager().get_center_queryset()
        except ComputeError as e:
            return render(request, 'error.html', {'errors': ['查询分中心时错误', str(e)]})

        context = {}
        context['center_id'] = center_id if center_id > 0 else None
        context['centers'] = centers
        context['tag_value'] = tag
        context['tags'] = Image.CHOICES_TAG
        context['sys_type_value'] = sys_type
        context['sys_types'] = Image.CHOICES_SYS_TYPE
        context['search'] = search
        context = self.get_page_context(request, queryset, context)
        return render(request, 'image_list.html', context=context)

    def get_page_context(self, request, vms_queryset, context: dict):
        # 分页显示
        paginator = NumsPaginator(request, vms_queryset, self.NUM_PER_PAGE)
        page_num = request.GET.get(paginator.page_query_name, 1)  # 获取页码参数，没有参数默认为1
        images_page = paginator.get_page(page_num)
        page_nav = paginator.get_page_nav(images_page)

        context['page_nav'] = page_nav
        context['images'] = images_page
        context['count'] = paginator.count
        return context
