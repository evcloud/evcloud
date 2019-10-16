#coding=utf-8
from .models import Device as DBDevice
from .models import DeviceType as DBDeviceType
from .device import Device

class DeviceError(Exception):
    '''
    PCIe设备相关错误定义
    '''
    def __init__(self, code:int=0, msg:str='', err=None):
        '''
        :param code: 错误码
        :param msg: 错误信息
        :param err: 错误对象
        '''
        self.code = code
        self.msg = msg
        self.err = err

    def __str__(self):
        return self.detail()

    def detail(self):
        '''错误详情'''
        if self.msg:
            return self.msg

        if self.err:
            return str(self.err)

        return '未知的错误'

class Manager(object):
    def get_device_by_id(self, device_id):
        return Device(db_id=device_id)

    def get_device_by_address(self, address):
        db = DBDevice.objects.filter(address = address)
        if not db.exists():
            raise DeviceError(msg='DEVICE BDF设备号有误')
        return Device(db=db[0])

    def get_device_list(self, group_id=None, host_id=None, vm_uuid=None):
        device_list = DBDevice.objects.all()
        if host_id:
            device_list = device_list.filter(host_id=host_id)
        elif group_id:
            device_list = device_list.filter(host__group_id=group_id)
        elif vm_uuid:
            device_list = device_list.filter(vm__uuid = vm_uuid)
        ret_list = []
        for device in device_list:
            ret_list.append(device(db=device))
        return ret_list

    def get_device_type_list(self):
        types = DBDeviceType.objects.all()
        ret_list = []
        for t in types:
            ret_list.append({
                'id': t.id,
                'name': t.name,
                })
        return ret_list



    
