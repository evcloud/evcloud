from datetime import datetime, timedelta

from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from logrecord.models import LogRecord
from utils.paginators import NumsPaginator


# Create your views here.

class LogRecordView(View):

    NUM_PER_PAGE = 100  # Show num per page
    def get(self, request):
        search = request.GET.get('search', '')
        queryset = LogRecord.objects.all()
        if search:
            queryset = queryset.filter(username__contains=search)

        context = self.get_list_context(request, queryset, context={'search': search})
        return render(request, 'log_list.html', context)

    def get_list_context(self, request, queryset, context: dict):
        # 分页显示
        paginator = NumsPaginator(request, queryset, self.NUM_PER_PAGE)
        page_num = request.GET.get(paginator.page_query_name, 1)  # 获取页码参数，没有参数默认为1
        page = paginator.get_page(page_num)
        page_nav = paginator.get_page_nav(page)

        context['page_nav'] = page_nav
        context['page'] = page
        context['count'] = paginator.count
        return context

    def post(self, request, *args, **kwargs):
        """清理半年前日志"""
        six_months_ago = datetime.now() - timedelta(days=180)
        queryset = LogRecord.objects.filter(create_time__lte=six_months_ago).all()
        try:
            queryset.delete()
        except Exception as e:
            return JsonResponse({'msg': f'删除失败: {str(e)}'}, json_dumps_params={'ensure_ascii': False}, status=400)

        return JsonResponse({'msg': '删除成功'}, json_dumps_params={'ensure_ascii': False})


