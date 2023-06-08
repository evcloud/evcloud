from django.shortcuts import render
from django.views.generic.base import View
from django.contrib.auth import get_user_model

from utils.errors import VmAccessDeniedError, VmNotExistError, Unsupported, NoMacIPError, NotFoundError
from .manager import VmManager, VmError, FlavorManager
from compute.managers import CenterManager, HostManager, GroupManager, ComputeError
from vdisk.manager import VdiskManager, VdiskError
from image.managers import ImageManager, ImageError
from image.models import Image
from device.manager import PCIDeviceManager, DeviceError
from utils.paginators import NumsPaginator
from network.managers import MacIPManager, VlanManager

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
                   'host_id': host_id if host_id > 0 else None, 'search': search, 'users': users, 'user_id': user_id}
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
            error = ComputeError(msg='查询分中心列表时错误', err=e)
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
                raise VmNotExistError(msg='【挂载硬盘时错误】【云主机不存在】')
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
                raise VmNotExistError(msg='【挂载硬盘时错误】【云主机不存在】')
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
                raise VmNotExistError(msg='云主机不存在')
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
                raise VmNotExistError(msg='云主机不存在')
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
                raise VmNotExistError(msg='云主机不存在')
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
                raise VmNotExistError(msg='云主机不存在')
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
                raise VmNotExistError(msg='【挂载PCI设备时错误】【云主机不存在】')
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
                raise VmNotExistError(msg='云主机不存在')
            except VmNotExistError as error:
                return error.render(request=request)

        if not vm.user_has_perms(request.user):
            try:
                raise VmAccessDeniedError(msg='没有此云主机的访问权限')
            except VmAccessDeniedError as error:
                return error.render(request=request)

        return render(request, 'vm_disk_expand.html', context={'vm': vm})


class VmShelveView(View):
    NUM_PER_PAGE = 20  # Show num per page

    def get(self, request, *args, **kwargs):
        user = request.user
        v_manager = VmManager()
        try:
            queryset = v_manager.filter_shelve_vm_queryset(user=user, is_superuser=user.is_superuser)
        except VmError as e:
            error = VmError(msg='查询虚拟机时错误', err=e)
            return error.render(request=request)

        # 分页显示
        paginator = NumsPaginator(request, queryset, self.NUM_PER_PAGE)
        page_num = request.GET.get(paginator.page_query_name, 1)  # 获取页码参数，没有参数默认为1
        vms_page = paginator.get_page(page_num)
        page_nav = paginator.get_page_nav(vms_page)

        context = {'page_nav': page_nav, 'vms': vms_page, 'count': paginator.count}

        return render(request, 'vm_shelve_list.html', context=context)


class VmUnshelveNetworkViews(View):
    """恢复 搁置虚拟机 空闲ip"""
    NUM_PER_PAGE = 20  # Show num per page

    def get(self, request, *args, **kwargs):
        # user = request.user
        vm_uuid = kwargs.get('vm_uuid', '')
        vm_manager = VmManager()
        vm = vm_manager.get_vm_by_uuid(vm_uuid=vm_uuid)
        if not vm:
            try:
                raise VmNotExistError(msg='云主机不存在')
            except VmNotExistError as error:
                return error.render(request=request)

        if not vm.user_has_perms(request.user):
            try:
                raise VmAccessDeniedError(msg='没有此云主机的访问权限')
            except VmAccessDeniedError as error:
                return error.render(request=request)

        if vm.vm_status != vm.VmStatus.SHELVE.value:
            try:
                raise Unsupported(msg='此云主机不支持此操作')
            except Unsupported as error:
                return error.render(request=request)

        macip_manager = MacIPManager()
        vlan_manager = VlanManager()
        try:
            mac_ip_queryset = self.get_free_mac_ip(vm=vm, vlan_manager=vlan_manager, macip_manager=macip_manager)
        except VmError as e:
            error = VmError(msg='查询可用ip资源时错误', err=e)
            return error.render(request=request)


        # 分页显示
        paginator = NumsPaginator(request, mac_ip_queryset, self.NUM_PER_PAGE)
        page_num = request.GET.get(paginator.page_query_name, 1)  # 获取页码参数，没有参数默认为1
        mac_page = paginator.get_page(page_num)
        page_nav = paginator.get_page_nav(mac_page)
        context = {'page_nav': page_nav, 'mac_ip': mac_page, 'count': paginator.count, 'vm_uuid': vm_uuid}
        return render(request, 'vm_unshelve.html', context=context)

    def get_free_mac_ip_by_vlan(self, macip_manager, vlan_queryset):
        """通过vlan 获取 可用的ip"""

        for vlan in vlan_queryset:
            mac_ip_queryset = macip_manager.get_free_ip_in_vlan(vlan_id=vlan.id)
            if mac_ip_queryset:
                return mac_ip_queryset
        raise NoMacIPError  # 没有mac ip 资源可用

    def get_vlan_by_center(self, vlan_manager, center):
        """通过 center 获取 vlan"""
        vlan_queryset = vlan_manager.get_center_vlan_queryset(center=center)

        return vlan_queryset

    def get_free_mac_ip(self, vm, vlan_manager, macip_manager):
        """获取可以的IP集合"""
        last_ip = vm.last_ip
        center = vm.center
        if last_ip:
            mac_queryset = macip_manager.filter_macip_queryset(vlan=last_ip.vlan, used=False)
            return mac_queryset
        elif center:
            vlan_queryset = self.get_vlan_by_center(vlan_manager=vlan_manager, center=center)
            try:
                mac_ip_queryset = self.get_free_mac_ip_by_vlan(macip_manager=macip_manager, vlan_queryset=vlan_queryset)
            except NoMacIPError as e:
                raise e
            return mac_ip_queryset
        else:
            raise NotFoundError(msg=f'信息缺失，无法找到可用资源')
