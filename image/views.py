from django.contrib.auth import get_user_model
from django.http import QueryDict, JsonResponse
from django.shortcuts import render, redirect, reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework import status

from ceph.models import GlobalConfig
from compute.managers import CenterManager, ComputeError
from logrecord.manager import user_operation_record
from network.managers import MacIPManager
from novnc.manager import NovncTokenManager
from utils.errors import NovncError, VmError, NoSuchImage
from utils.paginators import NumsPaginator
from vms.api import VmAPI
from vms.manager import FlavorManager
from vms.models import Vm
from .forms import ImageVmCreateFrom
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
        # 超级用户可以查看所有镜像，包括被禁用镜像
        auth = request.user
        try:
            api = ImageManager()
            queryset = api.filter_image_queryset(center_id=center_id, tag=tag, sys_type=sys_type, search=search,
                                                 all_no_filters=auth.is_superuser)
        except ImageError as e:
            error = ImageError(msg='查询镜像时错误', err=e)
            return error.render(request=request)

        try:
            centers = CenterManager().get_center_queryset()
        except ComputeError as e:
            error = ComputeError(msg='查询数据中心时错误', err=e)
            return error.render(request=request)

        context = {
            'center_id': center_id if center_id > 0 else None,
            'centers': centers,
            'tag_value': tag,
            'tags': Image.CHOICES_TAG,
            'sys_type_value': sys_type,
            'sys_types': Image.CHOICES_SYS_TYPE,
            'search': search
        }
        context = self.get_page_context(request, queryset, context)
        return render(request, 'image_list.html', context=context)

    def put(self, request):
        """
        更新镜像API
        """
        param = QueryDict(request.body)
        try:
            operation = param.get('operation')
            image_id = int(param.get('image_id'))
            target_image = Image.objects.filter(id=image_id).first()
            if operation == 'snap_update':
                target_image.create_snap()
                target_image.save()
                return JsonResponse(
                    {'code': status.HTTP_200_OK, 'code_text': '更新镜像成功', 'snap': target_image.snap},
                    status=status.HTTP_200_OK)
            elif operation == 'enable_update':
                target_image.enable = not target_image.enable
                target_image.save()
                return JsonResponse({'code': status.HTTP_200_OK, 'code_text': '镜像启用成功'},
                                    status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse(
                {'code': status.HTTP_500_INTERNAL_SERVER_ERROR, 'code_text': f'更新镜像操作失败，{str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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


class ImageDeleteView(View):
    """
    删除镜像视图
    """

    def get(self, request, *args, **kwargs):
        image = ImageManager().get_image_by_id(kwargs['id'])
        return render(request, 'image_delete.html', context={'image': image})

    def post(self, request, *args, **kwargs):
        try:
            image = ImageManager().get_image_by_id(kwargs['id'])
            if image:
                image.delete()
        except Exception as e:
            error = ImageError(msg='删除镜像错误', err=e)
            return error.render(request=request)

        return redirect(to=reverse('image:image-list'))


class ImageVmCreateView(View):
    """
    创建镜像虚拟机视图
    """

    def get(self, request, *args, **kwargs):

        image_id = str_to_int_or_default(kwargs.get('image_id', 0), 0)
        try:
            form = ImageVmCreateFrom(initial={'image_id': image_id})
        except Exception as e:
            error = NoSuchImage(msg=f'创建镜像虚拟机错误: {str(e)}', err=e)
            return error.render(request=request)

        context = {
            'form': form,
            'image': Image.objects.get(id=image_id)
        }
        return render(request, 'image_vm_create.html', context=context)

    def post(self, request, *args, **kwargs):
        """
         创建镜像虚拟机API
        """
        post = request.POST
        image_id = str_to_int_or_default(kwargs.get('image_id', 0), 0)

        data_center = post.get('data_center')
        group_image = post.get('group_image')
        host_image = post.get('host_image')
        vlan_id = post.get('vlan_image')
        mac_ip = post.get('mac_ip')
        vcpu = post.get('vcpu')
        mem = post.get('mem')

        # try:
        #     api = ImageManager()
        #     image = api.get_image_by_id(image_id)
        # except ImageError as e:
        #     error = ImageError(msg='查询镜像时错误', err=e)
        #     return error.render(request=request)

        # form = ImageVmCreateFrom(data=post, initial={'image_id': image_id})
        # if not form.is_valid():
        #     context = {
        #         'form': form,
        #         'image': image
        #     }
        #     return render(request, 'image_vm_create.html', context=context)

        api = VmAPI()

        validated_data = {'image_id': image_id, 'vcpu': int(vcpu),
                          'mem': int(mem), 'host_id': int(host_image),
                          'ipv4': mac_ip}

        try:
            api.create_vm_for_image(**validated_data)
        except Exception as e:
            error = ImageError(msg='创建镜像时错误', err=e)
            return error.render(request=request)
        return redirect(to=reverse('image:image-list'))


class ImageVmOperateView(View):
    '''
      镜像虚拟机操作API
    '''

    def post(self, request, *args, **kwargs):
        post = request.POST
        image_id = str_to_int_or_default(post['image_id'], 0)
        operation = post['operation']
        try:
            image_manager = ImageManager()
            image = image_manager.get_image_by_id(image_id)
            if not image:
                return JsonResponse({'code': status.HTTP_400_BAD_REQUEST, 'code_text': '镜像数据不存在'},
                                    status=status.HTTP_400_BAD_REQUEST)
        except ImageError as e:
            return JsonResponse({'code': status.HTTP_500_INTERNAL_SERVER_ERROR, 'code_text': f'镜像查询错误，{str(e)}'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if operation not in ['get-vnc-url', 'get-vm-status', 'start-vm', 'shutdown-vm', 'poweroff-vm', 'delete-vm', 'unshelve-vm', 'shelve-vm', 'delshelve-vm']:
            return JsonResponse({'code': status.HTTP_400_BAD_REQUEST, 'code_text': '镜像操作参数错误'},
                                status=status.HTTP_400_BAD_REQUEST)

        if operation == 'get-vnc-url':
            vnc_manager = NovncTokenManager()
            try:
                vnc_id, url = vnc_manager.generate_token(vmid=image.vm_uuid, hostip=image.vm_host.ipv4,
                                                         sshkey=image.vm_host.group.center.ssh_key)
                # url = request.build_absolute_uri(url)
                http_host = request.META['HTTP_HOST']
                # http_host = http_host.split(':')[0]
                http_scheme = 'https'
                global_config_obj = GlobalConfig().get_global_config()
                if global_config_obj:
                    http_scheme = global_config_obj['novncAccess']

                url = f'{http_scheme}://{http_host}{url}'
                return JsonResponse({'code': status.HTTP_200_OK, 'vnc_url': url, 'code_text': '获取VNC地址成功'},
                                    status=status.HTTP_200_OK)
            except NovncError as e:
                return JsonResponse(
                    {'code': status.HTTP_500_INTERNAL_SERVER_ERROR, 'code_text': f'创建虚拟机vnc失败，{str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if operation == 'start-vm':
            try:
                vm = Vm(uuid=image.vm_uuid, name=image.vm_uuid, vcpu=image.vm_vcpu, mem=image.vm_mem,
                        host=image.vm_host)
                api = VmAPI()
                api.vm_operations_for_image(vm=vm, op='start')
            except Exception as e:
                return JsonResponse(
                    {'code': status.HTTP_500_INTERNAL_SERVER_ERROR, 'code_text': f'虚拟机操作失败，{str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return JsonResponse({'code': status.HTTP_200_OK, 'msg': '虚拟机启动成功'}, status=status.HTTP_200_OK)

        if operation == 'shutdown-vm':
            vm = Vm(uuid=image.vm_uuid, name=image.vm_uuid, vcpu=image.vm_vcpu, mem=image.vm_mem, host=image.vm_host)
            api = VmAPI()
            api.vm_operations_for_image(vm=vm, op='shutdown')
            return JsonResponse({'code': status.HTTP_200_OK, 'msg': '虚拟机关闭成功'}, status=status.HTTP_200_OK)

        if operation == 'poweroff-vm':
            vm = Vm(uuid=image.vm_uuid, name=image.vm_uuid, vcpu=image.vm_vcpu, mem=image.vm_mem, host=image.vm_host)
            api = VmAPI()
            api.vm_operations_for_image(vm=vm, op='poweroff')
            return JsonResponse({'code': status.HTTP_200_OK, 'msg': '虚拟机关闭成功'}, status=status.HTTP_200_OK)

        if operation == 'unshelve-vm':
            try:
                self.unshelve_image_vm(request=request, image=image)
            except Exception as e:
                return JsonResponse({'code': status.HTTP_400_BAD_REQUEST, 'code_text': _('虚拟机恢复失败:') + str(e)},
                                    status=status.HTTP_400_BAD_REQUEST)
            return JsonResponse({'code': status.HTTP_200_OK, 'msg': _('虚拟机恢复成功')}, status=status.HTTP_200_OK)

        if operation == 'shelve-vm':
            try:
                self.shelve_image_vm(request=request, image=image)
            except Exception as e:
                return JsonResponse({'code': status.HTTP_400_BAD_REQUEST, 'code_text': _('虚拟机搁置失败:') + str(e)},
                                    status=status.HTTP_400_BAD_REQUEST)
            return JsonResponse({'code': status.HTTP_200_OK, 'msg': _('虚拟机搁置成功')}, status=status.HTTP_200_OK)

        if operation == 'delshelve-vm':
            try:
                self.delshelve_image_vm(request=request, image=image)
            except Exception as e:
                return JsonResponse({'code': status.HTTP_400_BAD_REQUEST, 'code_text': _('虚拟机删除失败:') + str(e)},
                                    status=status.HTTP_400_BAD_REQUEST)
            return JsonResponse({'code': status.HTTP_200_OK, 'msg': _('虚拟机删除成功')}, status=status.HTTP_200_OK)

        if operation == 'delete-vm':
            image.remove_image_vm()
            image.vm_uuid = None
            image.vm_mem = None
            image.vm_vcpu = None
            image.vm_host = None
            image.vm_mac_ip = None
            image.save(update_fields=['vm_uuid', 'vm_mem', 'vm_vcpu', 'vm_host', 'vm_mac_ip'])
            return JsonResponse({'code': status.HTTP_200_OK, 'msg': '镜像虚拟机删除成功'}, status=status.HTTP_200_OK)

        if operation == 'get-vm-status':
            if not image.vm_uuid and not image.vm_mac_ip:
                return JsonResponse({'code': status.HTTP_200_OK, 'code_text': '获取虚拟机状态成功',
                                     'status': {'status_code': 11, 'status_text': '尚未创建镜像虚拟机'}},
                                    status=status.HTTP_200_OK)
            elif not image.vm_uuid:
                return JsonResponse({'code': status.HTTP_200_OK, 'code_text': '获取虚拟机状态成功',
                                     'status': {'status_code': 12, 'status_text': '虚拟机已搁置'}},
                                    status=status.HTTP_200_OK)

            try:
                vm = Vm(uuid=image.vm_uuid, name=image.vm_uuid, vcpu=image.vm_vcpu, mem=image.vm_mem,
                        host=image.vm_host)
                api = VmAPI()
                code, msg = api.get_vm_status_for_image(vm=vm)
                return JsonResponse({'code': status.HTTP_200_OK, 'code_text': '获取虚拟机状态成功',
                                     'status': {'status_code': code, 'status_text': msg}}, status=status.HTTP_200_OK)
            except VmError as e:
                return JsonResponse(
                    {'code': status.HTTP_500_INTERNAL_SERVER_ERROR, 'code_text': f'获取虚拟机状态失败，{str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return JsonResponse({'code': status.HTTP_400_BAD_REQUEST, 'code_text': '操作失败，没有匹配的处理程序。'},
                            status=status.HTTP_400_BAD_REQUEST)

    def shelve_image_vm(self, request, image: Image):
        """搁置 镜像虚拟机 """

        image.remove_image_vm()  # 底层关机

        image.vm_uuid = None
        try:
            image.save(update_fields=['vm_uuid'])
        except Exception as e:
            raise ImageError(msg='搁置镜像虚拟机信息失败:' + str(e))
        request.query_params = {}
        user_operation_record.add_log(request=request, operation_content=f'镜像主机搁置, 云主机IP: {image.vm_mac_ip.ipv4}')

        return

    def unshelve_image_vm(self, request, image: Image):
        """恢复搁置 镜像虚拟机"""

        used = image.vm_mac_ip.can_used()

        if used is False:
            # ip 被使用
            mac_ip = MacIPManager().get_free_ip_in_vlan(vlan_id=image.vm_mac_ip.vlan_id).order_by('-id').first()
            if mac_ip is None:
                raise ImageError(msg='恢复搁置中的镜像主机时，无法查找到可用的IP信息')
            image.vm_mac_ip = mac_ip

        api = VmAPI()
        validated_data = {'image_id': image.id, 'vcpu': image.vm_vcpu,
                          'mem': image.vm_mem, 'host_id': image.vm_host_id,
                          'ipv4': image.vm_mac_ip.ipv4}

        try:
            api.create_vm_for_image(**validated_data)
        except Exception as e:
            error = ImageError(msg='创建镜像时错误:' + str(e))
            raise error

        request.query_params = {}
        user_operation_record.add_log(request=request, operation_content=f'恢复搁置中的镜像主机, 云主机IP: {image.vm_mac_ip.ipv4}')

        return

    def delshelve_image_vm(self, request, image: Image):
        """ 删除 搁置的 镜像虚拟机 """

        request.query_params = {}
        user_operation_record.add_log(request=request, operation_content=f'删除搁置中的镜像主机, 云主机IP: {image.vm_mac_ip.ipv4}')

        image.vm_host = None
        image.vm_mem = None
        image.vm_vcpu = None
        image.vm_mac_ip = None
        try:
            image.save(update_fields=['vm_host', 'vm_mem', 'vm_vcpu', 'vm_mac_ip'])
        except Exception as e:
            raise ImageError(msg='删除搁置镜像虚拟机信息失败:' + str(e))

        return
