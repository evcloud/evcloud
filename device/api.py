#coding=utf-8
from vms.api import VmAPI
from compute.api import HostAPI
from compute.api import GroupAPI
from .manager import Manager as DeviceManager

class DeviceAPI(object):
    def __init__(self, manager=None, vm_api=None, host_api=None, group_api=None):
        if manager:
            self.manager = manager
        else:
            self.manager = DeviceManager()
        if vm_api:
            self.vm_api = vm_api
        else:
            self.vm_api = VmAPI()
        if host_api:
            self.host_api = host_api
        else:
            self.host_api = HostAPI()
        if group_api:
            self.group_api = group_api
        else:
            self.group_api = GroupAPI()

    def get_device_list_by_host_id(self, host_id):
        return self.manager.get_device_list(host_id = host_id)

    def get_device_list_by_group_id(self, group_id):
        return self.manager.get_device_list(group_id=group_id)

    def get_device_by_id(self, device_id):
        return self.manager.get_device_by_id(device_id)

    def get_device_by_address(self, address):
        return self.manager.get_device_by_address(address)

    def get_device_list_by_vm_uuid(self, vm_uuid):
        return self.manager.get_device_list(vm_uuid=vm_uuid)
        
    def set_remarks(self, device_id, content):
        device = self.manager.get_device_by_id(device_id)
        return device.set_remarks(content)

    def mount(self, vm_id, device_id):
        device = self.manager.get_device_by_id(device_id)
        vm = self.vm_api.get_vm_by_uuid(vm_id)
        if vm.host_id != device.host_id:
            return False

        if device.mount(vm_id):
            if self.vm_api.attach_device(vm_id, device.xml_desc):
                return True
            device.umount()
        return False

    def umount(self, device_id):
        device = self.manager.get_device_by_id(device_id)
        if self.vm_api.vm_uuid_exists(device.vm):
            vm = self.vm_api.get_vm_by_uuid(device.vm)
            if vm and vm.host_id != device.host_id:
                return False
            if self.vm_api.detach_device(vm.uuid, device.xml_desc):
                if device.umount():
                    return True
                self.vm_api.attach_device(vm.uuid, device.xml_desc)
        else:
            if device.umount():
                return True
        return False
    