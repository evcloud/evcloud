#coding=utf-8

from compute.api import VmAPI
from compute.api import HostAPI
from compute.api import GroupAPI
from api.error import Error
from api.error import ERR_GPU_ID
from api.error import ERR_GPU_ADDRESS

from .manager import GPUManager

class GPUAPI(object):
    def __init__(self, manager=None, vm_api=None, host_api=None, group_api=None):
        if manager:
            self.manager = manager
        else:
            self.manager = GPUManager()
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

    def get_gpu_list_by_host_id(self, host_id):
        host = self.host_api.get_host_by_id(host_id)
        return self.manager.get_gpu_list(host_id = host_id)

    def get_gpu_list_by_group_id(self, group_id):
        group = self.group_api.get_group_by_id(group_id)
        return self.manager.get_gpu_list(group_id=group_id)

    def get_gpu_by_id(self, gpu_id):
        return self.manager.get_gpu_by_id(gpu_id)

    def get_gpu_by_address(self, address):
        return self.manager.get_gpu_by_address(address)

    def get_gpu_list_by_vm_uuid(self, vm_uuid):
        return self.manager.get_gpu_list(vm_uuid=vm_uuid)
        
    def set_remarks(self, gpu_id, content):
        gpu = self.manager.get_gpu_by_id(gpu_id)
        return gpu.set_remarks(content)

    def mount(self, vm_id, gpu_id):
        gpu = self.manager.get_gpu_by_id(gpu_id)
        vm = self.vm_api.get_vm_by_uuid(vm_id)
        if vm.host_id != gpu.host_id:
            return False
        if gpu.mount(vm_id):
            if self.vm_api.attach_device(vm_id, gpu.xml_desc):
                return True
            gpu.umount()
        return False

    def umount(self, gpu_id):
        gpu = self.manager.get_gpu_by_id(gpu_id)
        if self.vm_api.vm_uuid_exists(gpu.vm):
            vm = self.vm_api.get_vm_by_uuid(gpu.vm)
            if vm and vm.host_id != gpu.host_id:
                return False
            if self.vm_api.detach_device(vm.uuid, gpu.xml_desc):
                if gpu.umount():
                    return True
                self.vm_api.attach_device(vm.uuid, gpu.xml_desc)
        else:
            if gpu.umount():
                return True
        return False
    