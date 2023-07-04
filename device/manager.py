# coding=utf-8
from django.db.models import Q

from utils.ev_libvirt.virt import VirtError, VmDomain
from compute.managers import GroupManager, ComputeError, CenterManager, HostManager
from .models import PCIDevice
from .device import GPUDevice, HardDiskDevice
from utils.errors import DeviceError, AcrossGroupConflictError


class PCIDeviceManager:
    DeviceError = DeviceError

    def __init__(self):
        self._center_manager = CenterManager()
        self._group_manager = GroupManager()
        self._host_manager = HostManager()

    @staticmethod
    def get_device_queryset():
        """
        获取所有PCI设备的查询集
        :return: QuerySet()
        """
        return PCIDevice.objects.all()

    def get_device_by_id(self, device_id: int, related_fields=('host',)):
        """
        :return:
            PCIDevice()     # success
            None            # not exists
        :raises:  DeviceError
        """
        qs = self.get_device_queryset()
        try:
            if related_fields:
                qs = qs.select_related(*related_fields).all()
            return qs.filter(pk=device_id).first()
        except Exception as e:
            raise DeviceError(msg=str(e))

    def get_device_by_address(self, address: str):
        """
        :return:
            PCIDevice()     # success
            None            # not exists
        """
        return self.get_device_queryset().filter(address=address).first()

    def get_user_pci_queryset(self, user):
        """
        用户有访问权限的PCI设备查询集

        :param user: 用户对象
        :return:
            QuerySet()

        :raises: DeviceError
        """
        try:
            h_ids = GroupManager().get_user_host_ids(user=user)
            qs = self.get_device_queryset().filter(host__in=h_ids).all()
        except ComputeError as e:
            raise DeviceError(msg=str(e))
        return qs

    def get_pci_queryset_by_center(self, center):
        """
        分中心下的PCI设备查询集

        :param center: Center对象或id
        :return:
            QuerySet()

        :raises: DeviceError
        """
        try:
            group_ids = self._center_manager.get_group_ids_by_center(center)
            host_ids = self._group_manager.get_host_ids_by_group_ids(group_ids)
        except ComputeError as e:
            raise DeviceError(msg=str(e))

        return self.get_device_queryset().filter(host__in=host_ids).all()

    def get_user_pci_queryset_by_center(self, center, user):
        """
        用户有访问权限的，分中心下的PCI设备查询集

        :param center: Center对象或id
        :param user: 用户对象
        :return:
            QuerySet()

        :raises: DeviceError
        """
        try:
            group_ids = self._center_manager.get_user_group_ids_by_center(center=center, user=user)
            host_ids = self._group_manager.get_host_ids_by_group_ids(group_ids)
        except ComputeError as e:
            raise DeviceError(msg=str(e))

        return self.get_device_queryset().filter(host__in=host_ids).all()

    def get_pci_queryset_by_group(self, group):
        """
        宿主机组下的PCI设备查询集

        :param group: Group对象或id
        :return:
            QuerySet()

        :raises: DeviceError
        """
        try:
            ids = self._group_manager.get_enable_host_ids_by_group(group_or_id=group)
        except ComputeError as e:
            raise DeviceError(msg=str(e))

        return self.get_device_queryset().filter(host__in=ids).all()

    def get_user_pci_queryset_by_group(self, group, user):
        """
        用户有访问权限的，机组下的PCI设备查询集

        :param group: Group对象或id
        :param user: 用户对象
        :return:
            QuerySet()

        :raises: DeviceError
        """
        gm = self._group_manager

        try:
            group = gm.enforce_group_obj(group)
            if not group.user_has_perms(user=user):
                raise DeviceError(msg='无宿主机组的访问权限')
            ids = gm.get_all_host_ids_by_group(group_or_id=group)
        except ComputeError as e:
            raise DeviceError(msg=str(e))

        return self.get_device_queryset().filter(host__in=ids).all()

    def get_pci_queryset_by_host(self, host):
        """
        宿主机的PCI设备查询集

        :param host: Host对象或id
        :return:
            QuerySet()

        :raises: DeviceError
        """
        return self.get_device_queryset().filter(host=host).all()

    def get_user_pci_queryset_by_host(self, host, user):
        """
        用户有访问权限的，宿主机的PCI设备查询集

        :param host: Host对象或id
        :param user: 用户对象
        :return:
            QuerySet()

        :raises: DeviceError
        """
        try:
            host = self._host_manager.enforce_host_obj(host)
        except ComputeError as e:
            raise DeviceError(msg=str(e))

        if not host.user_has_perms(user=user):
            raise DeviceError(msg='无宿主机的访问权限')

        return self.get_device_queryset().filter(host=host).all()

    @staticmethod
    def device_wrapper(device: PCIDevice):
        """
        PCI设备对象的包装器

        :param device:PCI设备对象
        :return:
            BasePCIDevice子类     # GPUDevice

        :raises:  DeviceError
        """
        if device.type == device.TYPE_GPU:
            return GPUDevice(db=device)

        if device.type == device.TYPE_HD:
            return HardDiskDevice(db=device)

        raise DeviceError(msg='未知设备')

    def mount_to_vm(self, device: PCIDevice, vm):
        """
        挂载设备到虚拟机

        :param device: pci设备对象
        :param vm: 虚拟机对象
        :return:
            True    # success

        :raises: DeviceError
        """
        host = vm.host
        dev = self.device_wrapper(device)
        if dev.need_in_same_host():
            if dev.host_id != host.id:
                raise DeviceError.from_error(AcrossGroupConflictError(msg='设备和虚拟机不在同一宿主机'))

        try:
            dev.mount(vm=vm)
        except DeviceError as e:
            raise DeviceError(msg=f'与虚拟机建立挂载关系失败, {str(e)}')

        try:
            xml_desc = dev.xml_desc()
            if VmDomain(host_ip=host.ipv4, vm_uuid=vm.hex_uuid).attach_device(xml=xml_desc):
                return True
            raise VirtError(msg='挂载到虚拟机失败')
        except (VirtError, Exception) as e:
            try:
                dev.umount()
            except Exception:
                pass
            raise DeviceError(msg=str(e))

    def umount_from_vm(self, device: PCIDevice):
        """
        卸载设备从虚拟机

        :param device: pci设备对象
        :return:
            True    # success

        :raises: DeviceError
        """
        dev = self.device_wrapper(device)
        vm = dev.vm
        if not vm:
            return True

        host = vm.host
        xml_desc = dev.xml_desc
        domain = VmDomain(host_ip=host.ipv4, vm_uuid=vm.hex_uuid)
        try:
            if not domain.detach_device(xml=xml_desc):
                raise VirtError(msg='从虚拟机卸载设备失败')
        except VirtError as e:
            raise DeviceError(msg=str(e))

        try:
            dev.umount()
        except DeviceError as e:
            domain.attach_device(xml=xml_desc)
            raise DeviceError(msg=f'与虚拟机解除挂载关系失败, {str(e)}')

        return True

    def filter_pci_queryset(self, center_id: int = 0, group_id: int = 0, host_id: int = 0, type_id: int = 0,
                            search: str = '', user=None, all_no_filters: bool = False, related_fields: tuple = ()):
        """
        通过条件筛选虚拟机查询集

        :param center_id: 分中心id,大于0有效
        :param group_id: 机组id,大于0有效
        :param host_id: 宿主机id,大于0有效
        :param type_id: 设备类型id,大于0有效
        :param search: 关键字筛选条件
        :param user: 用户对象
        :param all_no_filters: 筛选条件都无效时；True: 返回所有； False: 抛出错误
        :param related_fields: 外键字段；外键字段直接一起获取，而不是惰性的用时再获取
        :return:
            QuerySet    # success

        :raise: DeviceError
        """
        if not related_fields:
            related_fields = ('host__group', 'vm__mac_ip')

        if center_id <= 0 and group_id <= 0 and host_id <= 0 and type_id <= 0 and not search:
            if user and user.id:
                return self.get_user_pci_queryset(user=user).select_related(*related_fields).all()

            if not all_no_filters:
                raise DeviceError(msg='无有效的查询条件')

            return self.get_device_queryset().select_related(*related_fields).all()

        queryset = None
        if host_id > 0:
            queryset = self.get_user_pci_queryset_by_host(host=host_id, user=user)
        elif group_id > 0:
            queryset = self.get_user_pci_queryset_by_group(group_id, user=user)
        elif center_id > 0:
            queryset = self.get_user_pci_queryset_by_center(center=center_id, user=user)

        if type_id > 0:
            if queryset is not None:
                queryset = queryset.filter(type=type_id).all()
            else:
                queryset = self.get_device_queryset().filter(type=type_id).all()

        if search:
            if queryset is not None:
                queryset = queryset.filter(Q(remarks__icontains=search) | Q(host__ipv4__icontains=search)).all()
            else:
                queryset = self.get_device_queryset().filter(
                    Q(remarks__icontains=search) | Q(host__ipv4__icontains=search)).all()

        return queryset.select_related(*related_fields).all()
