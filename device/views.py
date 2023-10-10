from django.shortcuts import render
from django.views import View

from compute.managers import CenterManager, GroupManager, ComputeError
from utils.errors import DeviceNotFound
from vms.manager import VmManager
from utils.paginators import NumsPaginator
from .manager import PCIDeviceManager, DeviceError
from .models import PCIDevice


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


class PCIView(View):
    """
    PCI Device类视图
    """
    NUM_PER_PAGE = 20   # Show num per page

    def get(self, request, *args, **kwargs):
        center_id = str_to_int_or_default(request.GET.get('center', 0), 0)
        group_id = str_to_int_or_default(request.GET.get('group', 0), 0)
        host_id = str_to_int_or_default(request.GET.get('host', 0), 0)
        type_id = str_to_int_or_default(request.GET.get('type', 0), 0)
        search = request.GET.get('search', '')
        user = request.user

        c_manager = CenterManager()
        g_manager = GroupManager()
        p_manager = PCIDeviceManager()
        p_manager._group_manager = g_manager
        try:
            queryset = p_manager.filter_pci_queryset(center_id=center_id, group_id=group_id, host_id=host_id,
                                                     search=search, type_id=type_id, user=user, all_no_filters=True)
        except DeviceError as e:
            error = DeviceError(msg='查询PCI设备时错误', err=e)
            return error.render(request=request)

        try:
            centers = c_manager.get_center_queryset()
            if center_id > 0:
                groups = c_manager.get_user_group_queryset_by_center(center_or_id=center_id, user=user)
            else:
                groups = c_manager.get_user_group_queryset(user=user)

            if group_id > 0:
                hosts = g_manager.get_all_host_queryset_by_group(group_id)
            else:
                hosts = None
        except ComputeError as e:
            error = ComputeError(msg='查询PCI设备时错误', err=e)
            return error.render(request=request)

        context = {'center_id': center_id if center_id > 0 else None, 'centers': centers, 'groups': groups,
                   'group_id': group_id if group_id > 0 else None, 'hosts': hosts,
                   'host_id': host_id if host_id > 0 else None, 'search': search, 'types': PCIDevice.CHOICES_TYPE,
                   'type_id': type_id}
        context = self.get_vms_list_context(request, queryset, context)
        return render(request, 'pci_list.html', context=context)

    def get_vms_list_context(self, request, vms_queryset, context: dict):
        # 分页显示
        paginator = NumsPaginator(request, vms_queryset, self.NUM_PER_PAGE)
        page_num = request.GET.get(paginator.page_query_name, 1)  # 获取页码参数，没有参数默认为1
        vms_page = paginator.get_page(page_num)
        page_nav = paginator.get_page_nav(vms_page)

        context['page_nav'] = page_nav
        context['devices'] = vms_page
        context['count'] = paginator.count
        return context


class PCIMountView(View):
    NUM_PER_PAGE = 20

    def get(self, request, *args, **kwargs):
        pci_id = kwargs.get('pci_id', '')
        search = request.GET.get('search', '')

        mgr = PCIDeviceManager()
        dev = mgr.get_device_by_id(device_id=pci_id, related_fields=('host__group', 'vm'))
        if not dev:
            try:
                raise DeviceNotFound(msg='【挂载PCI设备时错误】【PCI设备不存在】')
            except DeviceNotFound as error:
                return error.render(request=request)

        context = {'device': dev, 'search': search}
        # 如果已被挂载
        if dev.vm:
            return render(request, 'pci_mount.html', context=context)

        host = dev.host
        user = request.user

        vm_manager = VmManager()
        related_fields = ('user', 'image', 'mac_ip')
        try:
            if user.is_superuser:
                queryset = vm_manager.filter_vms_queryset(host_id=host.id, search=search,
                                                          related_fields=related_fields)
            else:
                queryset = vm_manager.filter_vms_queryset(host_id=host.id, search=search, user_id=user.id,
                                                          related_fields=related_fields)
        except vm_manager.VmError as e:
            error = vm_manager.VmError (msg='查询挂载虚拟机列表时错误', err=e)
            return error.render(request=request)

        context = self.get_vms_list_context(request=request, queryset=queryset, context=context)
        return render(request, 'pci_mount.html', context=context)

    def get_vms_list_context(self, request, queryset, context: dict):
        # 分页显示
        paginator = NumsPaginator(request, queryset, self.NUM_PER_PAGE)
        page_num = request.GET.get(paginator.page_query_name, 1)  # 获取页码参数，没有参数默认为1
        page = paginator.get_page(page_num)
        page_nav = paginator.get_page_nav(page)

        context['page_nav'] = page_nav
        context['vms'] = page
        context['count'] = paginator.count
        return context
