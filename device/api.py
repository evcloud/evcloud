#coding=utf-8

from compute.api import VmAPI
from compute.api import HostAPI
from .gpu import GPU
from .models import DBGPU
from .manager import GPUManager
from api.error import Error
from api.error import ERR_GPU_ID
from api.error import ERR_GPU_ADDRESS

class GPUAPI(object):
    def __init__(self, manager=None, vm_api=None, host_api=None):
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

    def get_gpu_list_by_host_id(self, host_id):
        host = self.host_api.get_host_by_id(host_id)
        db_list = DBGPU.objects.filter(host_id = host_id)
        ret_list = []
        for db in db_list:
            ret_list.append(GPU(db=db))
        return ret_list

    def get_gpu_by_id(self, gpu_id):
        db = DBGPU.objects.filter(pk = gpu_id)
        if not db.exists():
            raise Error(ERR_GPU_ID)
        return GPU(db=db[0])

    def get_gpu_by_address(self, address):
        db = DBGPU.objects.filter(address = address)
        if not db.exists():
            raise Error(ERR_GPU_ADDRESS)
        return GPU(db=db[0])

    def set_remarks(self, gpu_id, content):
        gpu = self.get_gpu_by_id(gpu_id)
        return gpu.set_remarks(content)

    def mount(self, vm_id, gpu_id):
        gpu = self.get_gpu_by_id(gpu_id)
        vm = self.vm_api.get_vm_by_uuid(vm_id)
        if vm.host_id != gpu.host_id:
            return False
        if self.vm_api.attach_device(vm_id, gpu.xml_desc):
            if gpu.mount(vm_id):
                return True
            self.vm_api.detach_device(vm_id, gpu.xml_desc)
        return False

    def umount(self, gpu_id):
        gpu = self.get_gpu_by_id(gpu_id)
        if self.vm_api.vm_uuid_exists(gpu.vm):
            vm = self.vm_api.get_vm_by_uuid(gpu.vm)
            if vm and vm.host_id != gpu.host_id:
                return False
            if gpu.umount():
                if self.vm_api.detach_device(vm.uuid, gpu.xml_desc):
                    return True
                gpu.mount(vm.uuid)
        else:
            if gpu.umount():
                return True
        return False
    