import json
import uuid

from django.db import transaction
from django.forms import model_to_dict
from django.http import QueryDict, HttpResponse, JsonResponse, Http404
from django.shortcuts import render, redirect, reverse
from django.views import View
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status

from ceph.models import CephCluster, CephPool
from compute.managers import CenterManager, ComputeError
from ceph.managers import get_rbd_manager, CephClusterManager, RadosError
from compute.models import Host
from novnc.manager import NovncTokenManager
from utils.errors import NovncError, VmError
from utils.paginators import NumsPaginator
from vms.models import Vm
from vms.vminstance import VmInstance
from .forms import ImageVmCreateFrom, ImageModelForm
from .managers import ImageManager, ImageError
from vms.manager import FlavorManager
from .models import Image, VmXmlTemplate
from vms.api import VmAPI

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
            image_id = int(param.get('image_id'))
            target_image = Image.objects.filter(id=image_id).first()
            target_image.create_newsnap = True
            target_image.save()
        except Exception as e:
            return JsonResponse({'code': status.HTTP_500_INTERNAL_SERVER_ERROR, 'code_text': f'更新镜像失败，{str(e)}'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return JsonResponse({'code': status.HTTP_200_OK, 'code_text': '更新镜像快照成功'},
                            status=status.HTTP_200_OK)

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


class ImageAddView(View):
    """
    创建镜像视图
    """

    def get(self, request, *args, **kwargs):
        local_host = Host.objects.get(ipv4='127.0.0.1')
        if local_host:
            form = ImageModelForm(form_type='add')
            vm_fields = ['vm_host', 'vm_uuid', 'vm_mac_ip', 'vm_vcpu', 'vm_mem']
            return render(request, 'image_add.html', context={'form': form, 'vm_fields': vm_fields})
        else:
            return render(request, 'error.html', {'errors': ['创建镜像虚拟机前必须创建IP为127.0.0.1的宿主机']})

    def post(self, request, *args, **kwargs):
        post = request.POST
        form = ImageModelForm(data=post, form_type='add')
        if not form.is_valid():
            vm_fields = ['vm_host', 'vm_uuid', 'vm_mac_ip', 'vm_vcpu', 'vm_mem']
            return render(request, 'image_add.html', context={'form': form, 'vm_fields': vm_fields})
        try:
            with transaction.atomic():
                image = form.save()
                api = VmAPI()
                validated_data = {'image_id': image.id, 'vcpu': image.vm_vcpu,
                                  'mem': image.vm_mem, 'host_id': image.vm_host.id,
                                  'ipv4': image.vm_mac_ip.ipv4}
                vm = api.create_vm_for_image(**validated_data)
                image.vm_uuid = vm.uuid
                image.save()
        except Exception as e:
            return render(request, 'error.html', {'errors': ['新增错误', str(e)]})
        return redirect(to=reverse('image:image-list'))


class ImageChangeView(View):
    """
    更新镜像视图
    """

    def get(self, request, *args, **kwargs):
        local_host = Host.objects.get(ipv4='127.0.0.1')
        if local_host:
            pk = kwargs.get('id')
            image = ImageManager().get_image_by_id(pk)
            if not image:
                return render(request, 'error.html', {'errors': [f'id 为{pk}的镜像不存在']})
            form = ImageModelForm(instance=image, form_type='change')
            vm_fields = ['vm_host', 'vm_uuid', 'vm_mac_ip', 'vm_vcpu', 'vm_mem']
            return render(request, 'image_change.html', context={'form': form, 'vm_fields': vm_fields})
        else:
            return render(request, 'error.html', {'errors': ['创建镜像虚拟机前必须创建IP为127.0.0.1的宿主机']})

    def post(self, request, *args, **kwargs):
        pk = kwargs.get('id')
        image = ImageManager().get_image_by_id(pk)
        form = ImageModelForm(request.POST, instance=ImageManager().get_image_by_id(pk), form_type='change')
        if not image:
            form.add_error(field=None, error=f'id 为{pk}的镜像不存在')
            vm_fields = ['vm_host', 'vm_uuid', 'vm_mac_ip', 'vm_vcpu', 'vm_mem']
            return render(request, 'image_change.html', context={'form': form, 'vm_fields': vm_fields})

        if not form.is_valid():
            vm_fields = ['vm_host', 'vm_uuid', 'vm_mac_ip', 'vm_vcpu', 'vm_mem']
            return render(request, 'image_change.html', context={'form': form, 'vm_fields': vm_fields})
        try:
            with transaction.atomic():
                new_image = form.save()
                if image.base_image != new_image.base_image:
                    vm = Vm(uuid=new_image.vm_uuid, name=new_image.vm_uuid, vcpu=new_image.vm_vcpu,
                            mem=new_image.vm_mem,
                            disk=new_image.base_image,
                            host=new_image.vm_host, mac_ip=new_image.vm_mac_ip, image=new_image)
                    api = VmAPI()
                    api.delete_vm_for_image(vm)
                    validated_data = {'image_id': new_image.id, 'vcpu': new_image.vm_vcpu,
                                      'mem': new_image.vm_mem, 'host_id': new_image.vm_host.id,
                                      'ipv4': new_image.vm_mac_ip.ipv4}
                    vm = api.create_vm_for_image(**validated_data)
                    new_image.vm_uuid = vm.uuid
                    new_image.save()
                else:
                    if image.vm_mem != new_image.vm_mem or image.vm_vcpu != new_image.vm_vcpu:
                        vm = Vm(uuid=image.vm_uuid, name=image.vm_uuid, vcpu=image.vm_vcpu, mem=image.vm_mem,
                                disk=image.base_image,
                                host=image.vm_host, mac_ip=image.vm_mac_ip, image=image)
                        api = VmAPI()
                        api.edit_vm_vcpu_mem_for_image(vm=vm, vcpu=new_image.vm_vcpu, mem=new_image.vm_mem)
        except Exception as e:
            form.add_error(field=None, error=f'更新镜像错误，{str(e)}')
            vm_fields = ['vm_host', 'vm_uuid', 'vm_mac_ip', 'vm_vcpu', 'vm_mem']
            return render(request, 'image_change.html', context={'form': form, 'vm_fields': vm_fields})
        return redirect(to=reverse('image:image-list'))


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
            return render(request, 'error.html', {'errors': [f'删除镜像错误{e}']})

        return redirect(to=reverse('image:image-list'))


class ImageVmCreateView(View):
    """
    创建镜像虚拟机视图
    """

    def get(self, request, *args, **kwargs):
        image_id = str_to_int_or_default(kwargs.get('image_id', 0), 0)
        form = ImageVmCreateFrom(initial={'image_id': image_id})
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
        try:
            api = ImageManager()
            image = api.get_image_by_id(image_id)
        except ImageError as e:
            return render(request, 'error.html', {'errors': ['查询镜像时错误', str(e)]})

        form = ImageVmCreateFrom(data=post)
        if not form.is_valid():
            context = {
                'form': form,
                'image': image
            }
            return render(request, 'image_vm_create.html', context=context)

        api = VmAPI()
        cleaned_data = form.cleaned_data
        validated_data = {'image_id': cleaned_data['image_id'], 'vcpu': cleaned_data['vcpu'],
                          'mem': cleaned_data['mem'], 'host_id': cleaned_data['host'].id,
                          'ipv4': cleaned_data['mac_ip'].ipv4}
        api.create_vm_for_image(**validated_data)

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

        if operation not in ['get-vnc-url', 'get-vm-status', 'start-vm', 'shutdown-vm', 'poweroff-vm']:
            return JsonResponse({'code': status.HTTP_400_BAD_REQUEST, 'code_text': '镜像操作参数错误'},
                                status=status.HTTP_400_BAD_REQUEST)

        if operation == 'get-vnc-url':
            vnc_manager = NovncTokenManager()
            try:
                vnc_id, url = vnc_manager.generate_token(vmid=image.vm_uuid, hostip=image.vm_host.ipv4)
                url = request.build_absolute_uri(url)
                return JsonResponse({'code': status.HTTP_200_OK, 'vnc_url': url, 'code_text': '获取VNC地址成功'},
                                    status=status.HTTP_200_OK)
            except NovncError as e:
                return JsonResponse(
                    {'code': status.HTTP_500_INTERNAL_SERVER_ERROR, 'code_text': f'创建虚拟机vnc失败，{str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if operation == 'start-vm':
            try:
                vm = Vm(uuid=image.vm_uuid, name=image.vm_uuid, vcpu=image.vm_vcpu, mem=image.vm_mem,
                        disk=image.base_image,
                        host=image.vm_host, mac_ip=image.vm_mac_ip, image=image)
                api = VmAPI()
                api.vm_operations_for_image(vm=vm, op='start')
            except Exception as e:
                return JsonResponse({'code': status.HTTP_500_INTERNAL_SERVER_ERROR, 'code_text': f'虚拟机操作失败，{str(e)}'},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return JsonResponse({'code': status.HTTP_200_OK, 'msg': '虚拟机启动成功'}, status=status.HTTP_200_OK)

        if operation == 'shutdown-vm':
            vm = Vm(uuid=image.vm_uuid, name=image.vm_uuid, vcpu=image.vm_vcpu, mem=image.vm_mem, disk=image.base_image,
                    host=image.vm_host, mac_ip=image.vm_mac_ip, image=image)
            api = VmAPI()
            api.vm_operations_for_image(vm=vm, op='shutdown')
            return JsonResponse({'code': status.HTTP_200_OK, 'msg': '虚拟机关闭成功'}, status=status.HTTP_200_OK)

        if operation == 'poweroff-vm':
            vm = Vm(uuid=image.vm_uuid, name=image.vm_uuid, vcpu=image.vm_vcpu, mem=image.vm_mem, disk=image.base_image,
                    host=image.vm_host, mac_ip=image.vm_mac_ip, image=image)
            api = VmAPI()
            api.vm_operations_for_image(vm=vm, op='poweroff')
            return JsonResponse({'code': status.HTTP_200_OK, 'msg': '虚拟机关闭成功'}, status=status.HTTP_200_OK)

        if operation == 'get-vm-status':
            if not image.vm_uuid:
                return JsonResponse({'code': status.HTTP_200_OK, 'code_text': '获取虚拟机状态成功',
                                     'status': {'status_code': 11, 'status_text': '尚未创建镜像云主机'}},
                                    status=status.HTTP_200_OK)
            try:
                vm = Vm(uuid=image.vm_uuid, name=image.vm_uuid, vcpu=image.vm_vcpu, mem=image.vm_mem,
                        disk=image.base_image,
                        host=image.vm_host, mac_ip=image.vm_mac_ip, image=image)
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
