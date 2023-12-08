from django.shortcuts import render
from django.views.generic.base import View
from django.contrib.auth import get_user_model

from utils.errors import VdiskNotExist
from vdisk.manager import VdiskManager, VdiskError
from compute.managers import CenterManager, GroupManager, ComputeError
from utils.paginators import NumsPaginator
from vms.manager import VmManager

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


class VdiskView(View):
    """
    云硬盘类视图
    """
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
            error = VdiskError(msg='查询云硬盘时错误', err=e)
            return error.render(request=request)

        try:
            c_manager = CenterManager()
            centers = c_manager.get_center_queryset()
            if center_id > 0:
                groups = c_manager.get_group_queryset_by_center(center_id)
            else:
                groups = GroupManager().get_group_queryset()
        except ComputeError as e:
            error = ComputeError(msg='查询机组时错误', err=e)
            return error.render(request=request)

        if group_id > 0:
            quotas = manager.get_quota_queryset_by_group(group_id)
        else:
            quotas = None

        context = {
            'centers': centers,
            'center_id': center_id if center_id > 0 else None,
            'groups': groups,
            'group_id': group_id if group_id > 0 else None,
            'quotas': quotas,
            'quota_id': quota_id if quota_id > 0 else None,
            'search': search,
            'users': users,
            'user_id': user_id
        }
        context = self.get_disks_list_context(request, queryset, context)
        return render(request, 'vdisk_list.html', context=context)

    def get_disks_list_context(self, request, queryset, context: dict):
        # 分页显示
        paginator = NumsPaginator(request, queryset, self.NUM_PER_PAGE)
        page_num = request.GET.get(paginator.page_query_name, 1)  # 获取页码参数，没有参数默认为1
        page = paginator.get_page(page_num)
        page_nav = paginator.get_page_nav(page)

        context['page_nav'] = page_nav
        context['vdisks'] = page
        context['count'] = paginator.count
        return context


class VdiskCreateView(View):
    """创建硬盘类视图"""
    def get(self, request, *args, **kwargs):
        center_id = str_to_int_or_default(request.GET.get('center_id', 0), 0)

        try:
            c_manager = CenterManager()
            centers = c_manager.get_center_queryset()
            if center_id == 0:
                if len(centers) > 0:
                    center_id = centers.first().id

            groups = None
            if center_id > 0:
                groups = c_manager.get_user_group_queryset_by_center(center_id, user=request.user)
        except ComputeError as e:
            error = ComputeError(msg='查询数据中心列表时错误', err=e)
            return error.render(request=request)

        context = {
            'center_id': center_id if center_id > 0 else None,
            'centers': centers,
            'groups': groups
        }
        return render(request, 'vdisk_create.html', context=context)


class DiskMountToVmView(View):
    """硬盘挂载到虚拟机类视图"""
    NUM_PER_PAGE = 20

    def get(self, request, *args, **kwargs):
        disk_uuid = kwargs.get('disk_uuid', '')
        search = request.GET.get('search', '')

        disk_manager = VdiskManager()
        disk = disk_manager.get_vdisk_by_uuid(uuid=disk_uuid, related_fields=('quota', 'quota__group', 'vm'))
        if not disk:
            try:
                raise VdiskNotExist(msg='【挂载硬盘时错误】【云硬盘不存在】')
            except VdiskNotExist as error:
                return error.render(request=request)

        context = {'disk': disk, 'search': search}
        # 如果硬盘已被挂载
        if disk.vm:
            return render(request, 'vdisk_mount_to_vm.html', context=context)

        group = disk.quota.group
        user = request.user

        vm_manager = VmManager()
        related_fields = ('user', 'image', 'mac_ip')
        try:
            if user.is_superuser:
                queryset = vm_manager.filter_vms_queryset(
                    group_id=group.id, search=search, related_fields=related_fields)
            else:
                queryset = vm_manager.filter_vms_queryset(
                    group_id=group.id, search=search, user_id=user.id, related_fields=related_fields)
        except vm_manager.VmError as e:
            error = vm_manager.VmError(msg='查询挂载虚拟机列表时错误', err=e)
            return error.render(request=request)

        context = self.get_vms_list_context(request=request, queryset=queryset, context=context)
        return render(request, 'vdisk_mount_to_vm.html', context=context)

    def get_vms_list_context(self, request, queryset, context: dict):
        # 分页显示
        paginator = NumsPaginator(request, queryset, self.NUM_PER_PAGE)
        page_num = request.GET.get(paginator.page_query_name, 1)  # 获取页码参数，没有参数默认为1
        vms_page = paginator.get_page(page_num)
        page_nav = paginator.get_page_nav(vms_page)

        context['page_nav'] = page_nav
        context['vms'] = vms_page
        context['count'] = paginator.count
        return context
