#coding=utf-8
from api.error import Error
from api.error import ERR_GPU_ID
from api.error import ERR_GPU_ADDRESS

from .models import DBGPU
from .gpu import GPU

class GPUManager(object):
    def gpu_id_exists(self, gpu_id):
        return DBGPU.objects.filter(pk=gpu_id).exists()

    def get_gpu_by_id(self, gpu_id):
        return GPU(db_id=gpu_id)

    def get_gpu_by_address(self, address):
        db = DBGPU.objects.filter(address = address)
        if not db.exists():
            raise Error(ERR_GPU_ADDRESS)
        return GPU(db=db[0])

    def get_gpu_list(self, group_id=None, host_id=None, vm_uuid=None):
        gpu_list = DBGPU.objects.all()
        if host_id:
            gpu_list = gpu_list.filter(host_id=host_id)
        elif group_id:
            gpu_list = gpu_list.filter(host__group_id=group_id)
        elif vm_uuid:
            gpu_list = gpu_list.filter(vm = vm_uuid)
        ret_list = []
        for gpu in gpu_list:
            ret_list.append(GPU(db=gpu))
        return ret_list



    
