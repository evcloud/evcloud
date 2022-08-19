from io import BytesIO

from django.shortcuts import render, redirect, reverse
from django.views import View
from django.http import Http404
from django.http import FileResponse
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.serializers import Serializer
from drf_yasg.utils import swagger_auto_schema

from utils.paginators import NumsPaginator
from .manager import VPNManager, VPNError
from .forms import VPNChangeFrom, VPNAddFrom


def change_vpn_view(request, vpn):
    initial = {'username': vpn.username, 'password': vpn.password,
               'active': vpn.active, 'remarks': vpn.remarks}
    form = VPNChangeFrom(initial=initial)
    return render(request, 'change.html', context={'form': form, 'vpn': vpn})


def add_vpn_view(request, pk: int):
    vpn = VPNManager().get_vpn_by_id(pk)
    return render(request, 'delete.html', context={'vpn': vpn})


class VPNView(View):
    NUM_PER_PAGE = 100  # Show num per page

    def get(self, request, *args, **kwargs):
        search = request.GET.get('search', '')
        mgr = VPNManager()
        qs = mgr.get_vpn_queryset()
        if search:
            qs = qs.filter(username__contains=search).all()

        context = self.get_list_context(request, qs, context={'search': search})
        return render(request, 'vpn_list.html', context)

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


class VPNChangeView(View):

    def get(self, request, *args, **kwargs):
        pk = kwargs.get('id')
        vpn = VPNManager().get_vpn_by_id(pk)
        if not vpn:
            raise Http404

        return change_vpn_view(request, vpn)

    def post(self, request, *args, **kwargs):
        post = request.POST
        form = VPNChangeFrom(data=post)
        if not form.is_valid():
            return render(request, 'change.html', context={'form': form})

        vpn = VPNManager().get_vpn_by_id(kwargs['id'])
        if not vpn:
            form.add_error(field=None, error='vpn不存在')
            render(request, 'change.html', context={'form': form, 'vpn': vpn})

        try:
            vpn = self.save_change(request, form, vpn)
        except Exception as e:
            form.add_error(field=None, error=str(e))
            return render(request, 'change.html', context={'form': form, 'vpn': vpn})

        _continue = post.get('_continue', None)
        if _continue is not None:       # 继续编辑
            return change_vpn_view(request, vpn)

        _addanother = post.get('_addanother', None)
        if _addanother is not None:     # 添加另一个
            return redirect(to=reverse('vpn:vpn-add'))

        return redirect(to=reverse('vpn:vpn-list'))

    @staticmethod
    def save_change(request, form, vpn):
        data = form.cleaned_data
        password = data['password']
        active = data['active']
        remarks = data['remarks']
        update_fields = []
        if vpn.password != password:
            vpn.password = password
            update_fields.append('password')

        if vpn.active != active:
            vpn.active = active
            update_fields.append('active')

        if vpn.remarks != remarks:
            vpn.remarks = remarks
            update_fields.append('remarks')

        if not update_fields:
            return vpn

        modified_user = request.user.username
        if vpn.modified_user != modified_user:
            vpn.modified_user = modified_user
            update_fields.append('modified_user')

        update_fields.append('modified_time')
        vpn.save(update_fields=update_fields)
        return vpn


class VPNAddView(View):
    def get(self, request, *args, **kwargs):
        form = VPNAddFrom(initial={'active': True})
        return render(request, 'add.html', context={'form': form})

    def post(self, request, *args, **kwargs):
        post = request.POST
        form = VPNAddFrom(data=post)
        if not form.is_valid():
            return render(request, 'add.html', context={'form': form})

        d = form.cleaned_data
        try:
            vpn = VPNManager().create_vpn(**d, create_user=request.user.username)
        except VPNError as e:
            form.add_error(field=None, error=str(e))
            return render(request, 'add.html', context={'form': form})

        _continue = post.get('_continue', None)
        if _continue is not None:       # 继续编辑
            return redirect(to=reverse('vpn:vpn-change', kwargs={'id': vpn.id}))

        _addanother = post.get('_addanother', None)
        if _addanother is not None:     # 添加另一个
            form = VPNAddFrom(initial={'active': True})
            return render(request, 'add.html', context={'form': form})

        return redirect(to=reverse('vpn:vpn-list'))


class VPNDeleteView(View):
    def get(self, request, *args, **kwargs):
        return add_vpn_view(request, kwargs['id'])

    def post(self, request, *args, **kwargs):
        vpn = VPNManager().get_vpn_by_id(kwargs['id'])
        if vpn:
            vpn.delete()

        return redirect(to=reverse('vpn:vpn-list'))


class VPNFileViewSet(viewsets.GenericViewSet):
    """
    VPN文件视图
    """
    permission_classes = []
    pagination_class = None
    serializer_class = Serializer

    @swagger_auto_schema(
        operation_summary='下载用户vpn配置文件'
    )
    @action(methods=['get'], detail=False, url_path='config', url_name='config')
    def vpn_config_file(self, request, *args, **kwargs):
        """
        下载用户vpn配置文件
        """
        obj = VPNManager().vpn_config_file()
        if not obj:
            return Response(data={'未添加vpn配置文件'}, status=status.HTTP_404_NOT_FOUND)

        filename = obj.filename if obj.filename else 'client.ovpn'
        content = obj.content.encode(encoding='utf-8')
        return FileResponse(BytesIO(initial_bytes=content), as_attachment=True, filename=filename)

    @swagger_auto_schema(
        operation_summary='下载用户vpn ca证书文件'
    )
    @action(methods=['get'], detail=False, url_path='ca', url_name='ca')
    def vpn_ca_file(self, request, *args, **kwargs):
        """
        下载用户vpn ca证书文件
        """
        obj = VPNManager().vpn_ca_file()
        if not obj:
            return Response(data={'未添加vpn ca证书文件'}, status=status.HTTP_404_NOT_FOUND)

        filename = obj.filename if obj.filename else 'ca.crt'
        content = obj.content.encode(encoding='utf-8')
        return FileResponse(BytesIO(initial_bytes=content), as_attachment=True, filename=filename)
