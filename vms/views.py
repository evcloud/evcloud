from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic.base import View
from django.contrib.auth import get_user_model

from utils.errors import VmAccessDeniedError, VmNotExistError, Unsupported, NoMacIPError, NotFoundError
from .api import VmAPI
from .manager import VmManager, VmError, FlavorManager, VmLogManager
from compute.managers import CenterManager, HostManager, GroupManager, ComputeError
from vdisk.manager import VdiskManager, VdiskError
from image.managers import ImageManager, ImageError
from image.models import Image
from device.manager import PCIDeviceManager, DeviceError
from utils.paginators import NumsPaginator
from network.managers import MacIPManager, VlanManager
from .models import AttachmentsIP

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


class VmsView(View):
    """
    虚拟机类视图
    """
    NUM_PER_PAGE = 20  # Show num per page

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
        else:  # 普通用户只能查看自己的虚拟机，无用户下拉框选项
            users = None
            user_id = auth.id

        v_manager = VmManager()
        try:
            queryset = v_manager.filter_vms_queryset(center_id=center_id, group_id=group_id, host_id=host_id,
                                                     search=search, user_id=user_id, all_no_filters=auth.is_superuser)

            queryset_shelve = v_manager.filter_shelve_vm_queryset(user_id=user_id, all_no_filters=auth.is_superuser)

        except VmError as e:
            error = VmError(msg='查询虚拟机时错误', err=e)
            return error.render(request=request)

        queryset = queryset.prefetch_related('vdisk_set')  # 反向预查询硬盘（避免多次访问数据库）
        try:
            c_manager = CenterManager()
            g_manager = GroupManager()
            centers = c_manager.get_center_queryset()
            if center_id > 0:
                groups = c_manager.get_group_queryset_by_center(center_id)
            else:
                groups = g_manager.get_group_queryset()

            if group_id > 0:
                hosts = g_manager.get_all_host_queryset_by_group(group_id)
            else:
                hosts = None
        except ComputeError as e:
            error = ComputeError(msg='查询虚拟机时错误', err=e)
            return error.render(request=request)

        context = {'center_id': center_id if center_id > 0 else None, 'centers': centers, 'groups': groups,
                   'group_id': group_id if group_id > 0 else None, 'hosts': hosts,
                   'host_id': host_id if host_id > 0 else None, 'search': search, 'users': users, 'user_id': user_id,
                   'shelve_count': queryset_shelve.count()}
        context = self.get_vms_list_context(request, queryset, context)
        return render(request, 'vms_list.html', context=context)

    def get_vms_list_context(self, request, vms_queryset, context: dict):
        # 分页显示
        paginator = NumsPaginator(request, vms_queryset, self.NUM_PER_PAGE)
        page_num = request.GET.get(paginator.page_query_name, 1)  # 获取页码参数，没有参数默认为1
        vms_page = paginator.get_page(page_num)
        page_nav = paginator.get_page_nav(vms_page)

        context['page_nav'] = page_nav
        context['vms'] = vms_page
        context['count'] = paginator.count
        return context


class VmCreateView(View):
    """创建虚拟机类视图"""

    def get(self, request, *args, **kwargs):
        center_id = str_to_int_or_default(request.GET.get('center_id', 0), 0)

        groups = None
        images = None
        try:
            c_manager = CenterManager()
            centers = c_manager.get_center_queryset()
            if center_id == 0:
                if len(centers) > 0:
                    center_id = centers.first().id

            if center_id > 0:
                images = ImageManager().get_image_queryset_by_center(center_id).filter(tag=Image.TAG_BASE, enable=True)
                groups = c_manager.get_user_group_queryset_by_center(center_id, user=request.user)
        except (ComputeError, ImageError) as e:
            error = ComputeError(msg='查询数据中心列表时错误', err=e)
            return error.render(request=request)

        context = {
            'center_id': center_id if center_id > 0 else None,
            'centers': centers,
            'groups': groups,
            'image_tags': Image.CHOICES_TAG,
            'images': images,
            'flavors': FlavorManager().get_user_flaver_queryset(user=request.user)
        }
        return render(request, 'vms_create.html', context=context)


class VmMountDiskView(View):
    """虚拟机挂载硬盘类视图"""
    NUM_PER_PAGE = 20

    def get(self, request, *args, **kwargs):
        vm_uuid = kwargs.get('vm_uuid', '')
        search = request.GET.get('search', '')

        vm_manager = VmManager()
        vm = vm_manager.get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=('host', 'host__group', 'image'))
        if not vm:
            try:
                raise VmNotExistError(msg='【挂载硬盘时错误】【虚拟机不存在】')
            except VmNotExistError as error:
                return error.render(request=request)

        group = vm.host.group
        user = request.user

        disk_manager = VdiskManager()
        related_fields = ('user', 'quota', 'quota__group')
        try:
            if user.is_superuser:
                queryset = disk_manager.filter_vdisk_queryset(group_id=group.id, search=search,
                                                              related_fields=related_fields)
            else:
                queryset = disk_manager.filter_vdisk_queryset(group_id=group.id, search=search,
                                                              user_id=user.id, related_fields=related_fields)
        except VdiskError as e:
            error = VdiskError(msg='查询硬盘列表时错误', err=e)
            return error.render(request=request)

        queryset = queryset.filter(vm=None).all()
        context = {'vm': vm, 'search': search}
        context = self.get_vdisks_list_context(request=request, queryset=queryset, context=context)
        return render(request, 'vm_mount_disk.html', context=context)

    def get_vdisks_list_context(self, request, queryset, context: dict):
        # 分页显示
        paginator = NumsPaginator(request, queryset, self.NUM_PER_PAGE)
        page_num = request.GET.get(paginator.page_query_name, 1)  # 获取页码参数，没有参数默认为1
        vms_page = paginator.get_page(page_num)
        page_nav = paginator.get_page_nav(vms_page)

        context['page_nav'] = page_nav
        context['vdisks'] = vms_page
        context['count'] = paginator.count
        return context


class VmDetailView(View):
    """虚拟机详情类视图"""

    def get(self, request, *args, **kwargs):
        vm_uuid = kwargs.get('vm_uuid', '')

        vm_manager = VmManager()
        vm = vm_manager.get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=('host__group', 'image__ceph_pool',
                                                                        'mac_ip__vlan'))
        if not vm:
            try:
                raise VmNotExistError(msg='【挂载硬盘时错误】【虚拟机不存在】')
            except VmNotExistError as error:
                return error.render(request=request)

        return render(request, 'vm_detail.html', context={'vm': vm})


class VmEditView(View):
    """虚拟机修改类视图"""

    def get(self, request, *args, **kwargs):
        vm_uuid = kwargs.get('vm_uuid', '')

        vm_manager = VmManager()
        vm = vm_manager.get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=(
            'host', 'host__group', 'host__group__center', 'image', 'mac_ip'))
        if not vm:
            try:
                raise VmNotExistError(msg='虚拟机不存在')
            except VmNotExistError as error:
                return error.render(request=request)

        context = {
            'flavors': FlavorManager().get_user_flaver_queryset(user=request.user),
            'vm': vm
        }
        return render(request, 'vm_edit.html', context=context)


class VmResetView(View):
    """虚拟机重置系统镜像类视图"""

    def get(self, request, *args, **kwargs):
        vm_uuid = kwargs.get('vm_uuid', '')

        vm_manager = VmManager()
        vm = vm_manager.get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=(
            'host', 'host__group', 'host__group__center', 'image', 'mac_ip'))
        if not vm:
            try:
                raise VmNotExistError(msg='虚拟机不存在')
            except VmNotExistError as error:
                return error.render(request=request)

        images = ImageManager().filter_image_queryset(
            center_id=vm.host.group.center_id, sys_type=0, tag=Image.TAG_BASE, search='')
        return render(request, 'vm_reset.html', context={'vm': vm, 'images': images})


class VmMigrateView(View):
    """虚拟机迁移类视图"""

    def get(self, request, *args, **kwargs):
        vm_uuid = kwargs.get('vm_uuid', '')

        vm_manager = VmManager()
        vm = vm_manager.get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=(
            'host', 'host__group', 'host__group__center', 'image', 'mac_ip'))
        if not vm:
            try:
                raise VmNotExistError(msg='虚拟机不存在')
            except VmNotExistError as error:
                return error.render(request=request)

        hosts = HostManager().get_hosts_by_group_id(group_id=vm.host.group_id)
        hosts = list(filter(lambda host: host.id != vm.host_id, hosts))
        return render(request, 'vm_migrate.html', context={'vm': vm, 'hosts': hosts})


class VmLiveMigrateView(View):
    """虚拟机动态迁移类视图"""

    def get(self, request, *args, **kwargs):
        vm_uuid = kwargs.get('vm_uuid', '')

        vm_manager = VmManager()
        vm = vm_manager.get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=(
            'host', 'host__group', 'host__group__center', 'image', 'mac_ip'))
        if not vm:
            try:
                raise VmNotExistError(msg='虚拟机不存在')
            except VmNotExistError as error:
                return error.render(request=request)

        hosts = HostManager().get_hosts_by_group_id(group_id=vm.host.group_id)
        hosts = list(filter(lambda host: host.id != vm.host_id, hosts))
        return render(request, 'vm_live_migrate.html', context={'vm': vm, 'hosts': hosts})


class VmMountPCIView(View):
    """虚拟机挂载PCI设备类视图"""
    NUM_PER_PAGE = 20

    def get(self, request, *args, **kwargs):
        vm_uuid = kwargs.get('vm_uuid', '')
        search = request.GET.get('search', '')

        vm_manager = VmManager()
        vm = vm_manager.get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=('host__group', 'image'))
        if not vm:
            try:
                raise VmNotExistError(msg='【挂载PCI设备时错误】【虚拟机不存在】')
            except VmNotExistError as error:
                return error.render(request=request)

        host = vm.host
        user = request.user

        mgr = PCIDeviceManager()
        try:
            queryset = mgr.filter_pci_queryset(host_id=host.id, search=search,
                                               user=user, related_fields=('host__group',))
        except DeviceError as e:
            error = DeviceError(msg='查询PCI设备列表时错误', err=e)
            return error.render(request=request)

        context = {'vm': vm, 'search': search}
        context = self.get_pci_list_context(request=request, queryset=queryset, context=context)
        return render(request, 'vm_mount_pci.html', context=context)

    def get_pci_list_context(self, request, queryset, context: dict):
        # 分页显示
        paginator = NumsPaginator(request, queryset, self.NUM_PER_PAGE)
        page_num = request.GET.get(paginator.page_query_name, 1)  # 获取页码参数，没有参数默认为1
        page = paginator.get_page(page_num)
        page_nav = paginator.get_page_nav(page)

        context['page_nav'] = page_nav
        context['devices'] = page
        context['count'] = paginator.count
        return context


class VmSysDiskExpandView(View):
    """虚拟机系统盘扩容类视图"""

    def get(self, request, *args, **kwargs):
        vm_uuid = kwargs.get('vm_uuid', '')

        vm_manager = VmManager()
        vm = vm_manager.get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=(
            'host', 'image__ceph_pool__ceph'))
        if not vm:
            try:
                raise VmNotExistError(msg='虚拟机不存在')
            except VmNotExistError as error:
                return error.render(request=request)

        if not vm.user_has_perms(request.user):
            try:
                raise VmAccessDeniedError(msg='没有此虚拟机的访问权限')
            except VmAccessDeniedError as error:
                return error.render(request=request)

        return render(request, 'vm_disk_expand.html', context={'vm': vm})


class VmShelveView(View):
    NUM_PER_PAGE = 20  # Show num per page

    def get(self, request, *args, **kwargs):
        user_id = str_to_int_or_default(request.GET.get('user', 0), 0)
        search = request.GET.get('search', '')

        v_manager = VmManager()

        # 超级用户可以有用户下拉框选项
        auth = request.user
        if auth.is_superuser:
            users = User.objects.all()
        else:  # 普通用户只能查看自己的虚拟机，无用户下拉框选项
            users = None
            user_id = auth.id

        try:
            queryset = v_manager.filter_shelve_vm_queryset(user_id=user_id, search=search,
                                                           all_no_filters=auth.is_superuser)
            queryset_normal = v_manager.filter_vms_queryset(user_id=user_id, all_no_filters=auth.is_superuser)
        except VmError as e:
            error = VmError(msg='查询虚拟机时错误', err=e)
            return error.render(request=request)

        queryset = queryset.prefetch_related('vdisk_set')  # 反向预查询硬盘（避免多次访问数据库）
        # 分页显示
        paginator = NumsPaginator(request, queryset, self.NUM_PER_PAGE)
        page_num = request.GET.get(paginator.page_query_name, 1)  # 获取页码参数，没有参数默认为1
        vms_page = paginator.get_page(page_num)
        page_nav = paginator.get_page_nav(vms_page)

        context = {'page_nav': page_nav, 'vms': vms_page, 'count': paginator.count, 'search': search, 'users': users,
                   'user_id': user_id, 'queryset_normal': queryset_normal.count()}

        return render(request, 'vm_shelve_list.html', context=context)


class VmUnShelveView(View):
    """恢复虚拟机类视图"""

    def get(self, request, *args, **kwargs):
        vm_uuid = kwargs.get('vm_uuid', '')
        vm = VmManager().get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=())
        if not vm:
            error = VmError(code=400, msg='查询错误，无虚拟机')
            return error.render(request=request)

        if not vm.user_has_perms(user=request.user):
            error = VmError(code=400, msg='当前用户没有权限访问此虚拟机。')
            return error.render(request=request)

        center_id = 0
        if vm.last_ip:
            center_id = vm.last_ip.vlan.group.center_id

        try:
            c_manager = CenterManager()
            centers = c_manager.get_center_queryset()
            if len(centers) > 0:
                center_id = centers.first().id
            groups = c_manager.get_user_group_queryset_by_center(center_id, user=request.user)
        except ComputeError as e:
            error = ComputeError(msg='查询数据中心列表时错误', err=e)
            return error.render(request=request)

        context = {
            'center_id': center_id if center_id > 0 else None,
            'centers': centers,
            'groups': groups,
            'vm_uuid': vm_uuid,
            'last_ip': vm.last_ip,
        }
        return render(request, 'vm_unshelve.html', context=context)


class VmAttachIPView(View):
    NUM_PER_PAGE = 20  # Show num per page

    def get(self, request, *args, **kwargs):
        vm_uuid = kwargs.get('vm_uuid', '')
        vlan_id = str_to_int_or_default(request.GET.get('vlan-select', 0), 0)
        search = request.GET.get('search', '')
        vm = VmManager().get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=('mac_ip',))

        if not vm.user_has_perms(user=request.user):
            error = VmError(code=400, msg='当前用户没有权限访问此虚拟机。')
            return error.render(request=request)

        if vlan_id != 0:

            qs = MacIPManager().get_free_ip_in_vlan(vlan_id=vlan_id, flag=True)
        else:
            qs = MacIPManager().get_free_ip_in_vlan(vlan_id=vm.mac_ip.vlan_id, flag=True)

        if search:
            qs = qs.filter(Q(ipv4__icontains=search) | Q(ipv6__icontains=search))

        vlan = VlanManager().get_vlan_queryset()

        context = self.get_ip_list_context(request, qs, context={'vm_uuid': vm_uuid, 'vlan_id': vm.mac_ip.vlan_id,
                                                                 'vm': vm, 'vlan': vlan})
        return render(request, 'vm_attach_ip_list.html', context=context)

    def get_ip_list_context(self, request, queryset, context: dict):
        # 分页显示
        paginator = NumsPaginator(request, queryset, self.NUM_PER_PAGE)
        page_num = request.GET.get(paginator.page_query_name, 1)  # 获取页码参数，没有参数默认为1
        mac_page = paginator.get_page(page_num)
        page_nav = paginator.get_page_nav(mac_page)

        context['page_nav'] = page_nav
        context['mac_ip'] = mac_page
        context['count'] = paginator.count
        return context


class VmDetachIPView(View):
    NUM_PER_PAGE = 20  # Show num per page

    def get(self, request, *args, **kwargs):
        vm_uuid = kwargs.get('vm_uuid', '')
        vm = VmManager().get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=('mac_ip',))

        if not vm.user_has_perms(user=request.user):
            error = VmError(code=400, msg='当前用户没有权限访问此虚拟机。')
            return error.render(request=request)

        use_ip = AttachmentsIP.objects.select_related('sub_ip').filter(vm=vm).all()

        context = self.get_ip_list_context(request, use_ip, context={'vm_uuid': vm_uuid, 'vm': vm})
        return render(request, 'vm_detach_ip_list.html', context=context)

    def get_ip_list_context(self, request, queryset, context: dict):
        # 分页显示
        paginator = NumsPaginator(request, queryset, self.NUM_PER_PAGE)
        page_num = request.GET.get(paginator.page_query_name, 1)  # 获取页码参数，没有参数默认为1
        mac_page = paginator.get_page(page_num)
        page_nav = paginator.get_page_nav(mac_page)

        context['page_nav'] = page_nav
        context['mac_ip'] = mac_page
        context['count'] = paginator.count
        return context


class VmImageRelease(View):
    """镜像发布"""

    def get(self, request, *args, **kwargs):
        vm_uuid = kwargs.get('vm_uuid', '')
        vm = VmManager().get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=('image',))
        context = {'vm_uuid': vm_uuid, 'vm': vm, 'image': vm.image}
        return render(request, 'vm_image_release.html', context=context)

    def post(self, request, *args, **kwargs):
        """
        1. 获取vm
        2. 克隆一个快照 name:test1
        3. flatten test1 这个快照
        4. 成功后信息写入数据库 操作系统镜像
        5. 成功返回
        """
        vm_uuid = kwargs.get('vm_uuid', '')
        try:
            vm = VmManager().get_vm_by_uuid(vm_uuid=vm_uuid, related_fields=('image',))
        except Exception as e:
            error = VmError(code=400, msg=str(e))
            return error.render(request=request)

        image_name = request.POST.get('image_name')
        if not image_name:
            # error = VmError(code=400, msg=f'镜像名称不能为空。')
            # return error.render(request=request)
            JsonResponse.status_code = 400
            return JsonResponse({'status': 400, 'msg': f'镜像名称不能为空。'}, json_dumps_params={'ensure_ascii': False})

        image_name = '-user_' + image_name  # 新的镜像名称

        vm_api = VmAPI()
        log_manager = VmLogManager()

        user = request.user.username
        try:

            vm_api.vm_user_release_image(vm=vm, new_image_name=image_name, user=user, log_manager=log_manager)
        except Exception as e:
            # error = VmError(code=400, msg=str(e))
            # return error.render(request=request)
            JsonResponse.status_code = 400
            return JsonResponse({'status': 400, 'msg': str(e)}, json_dumps_params={'ensure_ascii': False})

        # 将新数据写入数据库

        image_label = request.POST.get('image_label')  # 镜像标签
        image_os_type = request.POST.get('image_os_type')  # 系统类型
        image_os_release = request.POST.get('image_os_release')  # 系统发行版本
        image_os_version = request.POST.get('image_os_version')  # 系统发行编号
        image_os_architecture = request.POST.get('image_os_architecture')  # 系统架构
        image_os_boot_mode = request.POST.get('image_os_boot_mode')  # 系统启动方式
        image_size = request.POST.get('image_size')  # 镜像大小
        image_default_user = request.POST.get('image_default_user')  # 系统默认登录用户名
        image_default_password = request.POST.get('image_default_password')  # 系统默认登录密码
        image_desc = request.POST.get('image_desc')  # 描述
        image_enable = request.POST.get('image_enable')  # 启用
        if image_enable == 'true':
            image_enable = True
        else:
            image_enable = False

        user_id = request.user.id
        try:
            # 镜像创建虚拟机不占用服务器 cpu 和 mem , 使用系统，不使用大业内存
            Image.objects.create(
                name=image_name,
                sys_type=int(image_os_type),
                version=image_os_version,
                release=image_os_release,
                architecture=int(image_os_architecture),
                boot_mode=int(image_os_boot_mode),
                ceph_pool=vm.ceph_pool,
                tag=int(image_label),
                base_image=image_name,
                enable=image_enable,
                xml_tpl=vm.image.xml_tpl,
                user_id=user_id,
                desc=image_desc,
                default_user=image_default_user,
                default_password=image_default_password,
                size=int(image_size)
            )
        except Exception as e:
            # error = ImageError(code=400, msg=f'image: {image_name} exists, the entered data cannot be saved. '
            #                                  f'Please contact the administrator.')
            # return error.render(request=request)

            msg = f'发布镜像数据保存失败，详细情况 ==》 用户：{user} 镜像名称：{image_name} 失败原因：{str(e)}'
            log_manager.add_log(title=f'发布镜像失败：{image_name}', about=log_manager.about.ABOUT_NORMAL, text=msg)

            JsonResponse.status_code = 400
            return JsonResponse({'status': 400,
                                 'msg': f'image: {image_name} exists, the entered data cannot be saved.Please contact the administrator.'},
                                json_dumps_params={'ensure_ascii': False})

        return JsonResponse({'msg': f'image: {image_name} release success.', })
