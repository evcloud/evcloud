#coding=utf-8
from django.db.models import Q

from utils.ev_libvirt.virt import VirtAPI, VirtError
from compute.managers import GroupManager, ComputeError, CenterManager
from .models import PCIDevice
from .device import GPUDevice, DeviceError


class PCIDeviceManager:
    DeviceError = DeviceError

    def get_device_queryset(self):
        '''
        获取所有PCI设备的查询集
        :return: QuerySet()
        '''
        return PCIDevice.objects.all()

    def get_device_by_id(self, device_id:int, related_fields=('host',)):
        '''
        :return:
            PCIDevice()     # success
            None            # not exists
        :raises:  DeviceError
        '''
        qs = self.get_device_queryset()
        try:
            if related_fields:
                qs = qs.select_related(*related_fields).all()
            return qs.filter(pk=device_id).first()
        except Exception as e:
            raise DeviceError(msg=str(e))

    def get_device_by_address(self, address:str):
        '''
        :return:
            PCIDevice()     # success
            None            # not exists
        '''
        return self.get_device_queryset().filter(address=address).first()

    def get_pci_queryset_by_center(self, center):
        """
        分中心下的PCI设备查询集

        :param center: Center对象或id
        :return:
            QuerySet()

        :raises: DeviceError
        """
        try:
            group_ids = CenterManager().get_group_ids_by_center(center)
            host_ids = GroupManager().get_hsot_ids_by_group_ids(group_ids)
        except ComputeError as e:
            raise DeviceError(msg=str(e))

        return self.get_device_queryset().filter(host__in=host_ids).all()

    def get_pci_queryset_by_group(self, group):
        '''
        宿主机组下的PCI设备查询集

        :param group: Group对象或id
        :return:
            QuerySet()

        :raises: DeviceError
        '''
        try:
            ids = GroupManager().get_host_ids_by_group(group_or_id=group)
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

    def device_wrapper(self, device:PCIDevice):
        '''
        PCI设备对象的包装器

        :param device:PCI设备对象
        :return:
            BasePCIDevice子类     # GPUDevice

        :raises:  DeviceError
        '''
        if device.type == device.TYPE_GPU:
            return GPUDevice(db=device)

        return DeviceError(msg='未知设备')

    def mount_to_vm(self, device: PCIDevice, vm):
        '''
        挂载设备到虚拟机

        :param device: pci设备对象
        :param vm: 虚拟机对象
        :return:
            True    # success

        :raises: DeviceError
        '''
        host = vm.host
        dev = self.device_wrapper(device)
        if dev.need_in_same_host():
            if dev.host_id != host.id:
                raise DeviceError(msg='设备和虚拟机不在同一宿主机')

        if dev.mount(vm=vm):
            raise DeviceError(msg='与虚拟机建立挂载关系失败')

        xml_desc = dev.xml_desc
        try:
            if VirtAPI().attach_device(host_ipv4=host.ipv4, vm_uuid=vm.hex_uuid, xml=xml_desc):
                return True
            raise VirtError(msg='挂载到虚拟机失败')
        except VirtError as e:
            dev.umount()
            raise DeviceError(msg=str(e))

    def umount_from_vm(self, device: PCIDevice):
        '''
        卸载设备从虚拟机

        :param device: pci设备对象
        :return:
            True    # success

        :raises: DeviceError
        '''
        dev = self.device_wrapper(device)
        vm = dev.vm
        if not vm:
            return True

        host = vm.host
        xml_desc = dev.xml_desc
        try:
            if not VirtAPI().detach_device(host_ipv4=host.ipv4, vm_uuid=vm.hex_uuid, xml=xml_desc):
                raise VirtError(msg='从虚拟机卸载设备失败')
        except VirtError as e:
            raise DeviceError(msg=str(e))

        if dev.umount():
            return True

        raise DeviceError(msg='虚拟机解除挂载关系失败')

    def filter_pci_queryset(self, center_id: int = 0, group_id: int = 0, host_id: int = 0, type_id: int = 0,
                            search: str = '', all_no_filters: bool = False, related_fields: tuple = ()):
        """
        通过条件筛选虚拟机查询集

        :param center_id: 分中心id,大于0有效
        :param group_id: 机组id,大于0有效
        :param host_id: 宿主机id,大于0有效
        :param type_id: 设备类型id,大于0有效
        :param search: 关键字筛选条件
        :param all_no_filters: 筛选条件都无效时；True: 返回所有； False: 抛出错误
        :param related_fields: 外键字段；外键字段直接一起获取，而不是惰性的用时再获取
        :return:
            QuerySet    # success

        :raise: DeviceError
        """
        if not related_fields:
            related_fields = ('host__group', 'vm__mac_ip')

        if center_id <= 0 and group_id <= 0 and host_id <= 0 and type_id <= 0 and not search:
            if not all_no_filters:
                raise DeviceError(msg='无有效的查询条件')

            return self.get_device_queryset().select_related(*related_fields).all()

        queryset = None
        if host_id > 0:
            queryset = self.get_pci_queryset_by_host(host=host_id)
        elif group_id > 0:
            queryset = self.get_pci_queryset_by_group(group_id)
        elif center_id > 0:
            queryset = self.get_pci_queryset_by_center(center_id)

        if type_id > 0:
            if queryset is not None:
                queryset = queryset.filter(type=type_id).all()
            else:
                queryset = self.get_device_queryset().filter(type=type_id).all()

        if search:
            if queryset is not None:
                queryset = queryset.filter(Q(remarks__icontains=search) | Q(host__ipv4__icontains=search)).all()
            else:
                queryset = self.get_device_queryset().filter(Q(remarks__icontains=search) | Q(host__ipv4__icontains=search)).all()

        return queryset.select_related(*related_fields).all()
