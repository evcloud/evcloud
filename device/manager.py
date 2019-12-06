#coding=utf-8
from utils.ev_libvirt.virt import VirtAPI, VirtError
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
        return self.get_device_queryset().filter(address = address).first()

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

    def mount_to_vm(self, device:PCIDevice, vm):
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
