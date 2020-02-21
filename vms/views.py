from django.shortcuts import render
from django.views.generic.base import View
from django.contrib.auth import get_user_model

from .manager import VmManager, VmError
from compute.managers import CenterManager, HostManager, GroupManager, ComputeError
from network.managers import VlanManager
from vdisk.manager import VdiskManager, VdiskError
from image.managers import ImageManager, ImageError
from image.models import Image
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
            g_manager = GroupManager()
            centers = c_manager.get_center_queryset()
            if center_id > 0:
                groups = c_manager.get_group_queryset_by_center(center_id)
            else:
                groups = g_manager.get_group_queryset()

            if group_id > 0:
                hosts = g_manager.get_host_queryset_by_group(group_id)
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
        context['vms'] = vms_page
        context['count'] = paginator.count
        return context


class VmCreateView(View):
    '''创建虚拟机类视图'''
    def get(self, request, *args, **kwargs):
        center_id = str_to_int_or_default(request.GET.get('center_id', 0), 0)

        groups = None
        images = None
        try:
            c_manager = CenterManager()
            centers = c_manager.get_center_queryset()
            if center_id > 0:
                images = ImageManager().get_image_queryset_by_center(center_id).filter(tag=Image.TAG_BASE)
                groups = c_manager.get_user_group_queryset_by_center(center_id, user=request.user)
        except (ComputeError, ImageError) as e:
            return render(request, 'error.html', {'errors': ['查询分中心列表时错误', str(e)]})

        context = {}
        context['center_id'] = center_id if center_id > 0 else None
        context['centers'] = centers
        context['groups'] = groups
        context['image_tags'] = Image.CHOICES_TAG
        context['images'] = images
        context['vlans'] = VlanManager().get_vlan_queryset()
        return render(request, 'vms_create.html', context=context)


class VmMountDiskView(View):
    '''虚拟机挂载硬盘类视图'''
    NUM_PER_PAGE = 20

    def get(self, request, *args, **kwargs):
        vm_uuid = kwargs.get('vm_uuid', '')
        search = request.GET.get('search', '')

        vm_manager = VmManager()
        vm = vm_manager.get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=('host', 'host__group', 'image'))
        if not vm:
            return render(request, 'error.html', {'errors': ['挂载硬盘时错误', '云主机不存在']})

        group = vm.host.group
        user = request.user

        disk_manager = VdiskManager()
        related_fields = ('user', 'quota', 'quota__group')
        try:
            if user.is_superuser:
                queryset = disk_manager.filter_vdisk_queryset(group_id=group.id, search=search, related_fields=related_fields)
            else:
                queryset = disk_manager.filter_vdisk_queryset(group_id=group.id, search=search, user_id=user.id, related_fields=related_fields)
        except VdiskError as e:
            return render(request, 'error.html', {'errors': ['查询分中心列表时错误', str(e)]})
        queryset = queryset.filter(vm=None).all()
        context = {}
        context['vm'] = vm
        context['search'] =search
        context = self.get_vdisks_list_context(request=request, queryset=queryset, context=context)
        return render(request, 'vm_mount_disk.html', context=context)

    def get_vdisks_list_context(self, request, queryset, context:dict):
        # 分页显示
        paginator = NumsPaginator(request, queryset, self.NUM_PER_PAGE)
        page_num = request.GET.get('page', 1)  # 获取页码参数，没有参数默认为1
        vms_page = paginator.get_page(page_num)
        page_nav = paginator.get_page_nav(vms_page)

        context['page_nav'] = page_nav
        context['vdisks'] = vms_page
        context['count'] = paginator.count
        return context


class VmDetailView(View):
    '''虚拟机详情类视图'''
    def get(self, request, *args, **kwargs):
        vm_uuid = kwargs.get('vm_uuid', '')

        vm_manager = VmManager()
        vm = vm_manager.get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=('host', 'host__group', 'image'))
        if not vm:
            return render(request, 'error.html', {'errors': ['挂载硬盘时错误', '云主机不存在']})

        return render(request, 'vm_detail.html', context={'vm': vm})


class VmEditView(View):
    '''虚拟机修改类视图'''
    def get(self, request, *args, **kwargs):
        vm_uuid = kwargs.get('vm_uuid', '')

        vm_manager = VmManager()
        vm = vm_manager.get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=('host', 'host__group', 'host__group__center', 'image', 'mac_ip'))
        if not vm:
            return render(request, 'error.html', {'errors': ['云主机不存在']})

        return render(request, 'vm_edit.html', context={'vm': vm})


class VmResetView(View):
    """虚拟机重置系统镜像类视图"""
    def get(self, request, *args, **kwargs):
        vm_uuid = kwargs.get('vm_uuid', '')

        vm_manager = VmManager()
        vm = vm_manager.get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=('host', 'host__group', 'host__group__center', 'image', 'mac_ip'))
        if not vm:
            return render(request, 'error.html', {'errors': ['云主机不存在']})

        images = ImageManager().get_image_queryset_by_tag(tag=Image.TAG_BASE)
        return render(request, 'vm_reset.html', context={'vm': vm, 'images': images})


class VmMigrateView(View):
    """虚拟机迁移类视图"""
    def get(self, request, *args, **kwargs):
        vm_uuid = kwargs.get('vm_uuid', '')

        vm_manager = VmManager()
        vm = vm_manager.get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=('host', 'host__group', 'host__group__center', 'image', 'mac_ip'))
        if not vm:
            return render(request, 'error.html', {'errors': ['云主机不存在']})

        hosts = HostManager().get_hosts_by_group_id(group_id=vm.host.group_id)
        return render(request, 'vm_migrate.html', context={'vm': vm, 'hosts': hosts})
