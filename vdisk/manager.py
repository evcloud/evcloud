#coding=utf-8
import uuid
from .models import Vdisk as DBVdisk
from .vdisk import Vdisk

class VdiskError(Exception):
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
    def create_vdisk(self, cephpool, size, group_id=None, vdisk_id=None):
        if not vdisk_id:
            vdisk_id = str(uuid.uuid4())
        print(cephpool, vdisk_id, size)
        create_success = cephpool.create(vdisk_id, size)
        if create_success:
            try:
                db = DBVdisk()
                db.uuid = vdisk_id
                db.size = size
                db.cephpool_id = cephpool.id
                db.group_id = group_id
                db.save()        
            except Exception as e:
                cephpool.rm(vdisk_id)
                raise VdiskError(msg=f'云硬盘创建失败，写入数据库失败,{str(e)}')
            else:
                return vdisk_id
        else:
            raise VdiskError(msg='ceph create操作失败')

    def get_vdisk_list(self, user_id=None, creator=None, cephpool_id=None, group_id=None, vm_uuid=None):
        vdisk_list = DBVdisk.objects.all().order_by('-create_time')
        if user_id:
            vdisk_list = vdisk_list.filter(user_id=user_id)
        if creator:
            vdisk_list = vdisk_list.filter(creator=creator)
        if cephpool_id:
            vdisk_list = vdisk_list.filter(cephpool_id=cephpool_id)
        if group_id:
            vdisk_list = vdisk_list.filter(group_id=group_id)
        if vm_uuid:
            vdisk_list = vdisk_list.filter(vm=vm_uuid)
        ret_list = []
        for vdisk in vdisk_list:
            ret_list.append(Vdisk(db=vdisk))
        return ret_list

    def get_vdisk_quota_by_group_id(self, group_id):
        return 0

    def get_group_quota_by_group_id(self, group_id):
        return 0

    def set_vdisk_quota(self, size):
        '''目前使用Django admin模块维护数据，暂不使用此函数'''
        return False

    def set_group_quota(self, size):
        '''目前使用Django admin模块维护数据，暂不使用此函数'''
        return False

    def get_vdisk_by_id(self, vdisk_id):
        try:
            vdisk = DBVdisk.objects.get(uuid = vdisk_id)
        except:
            raise VdiskError(msg='云硬盘ID有误')
        return Vdisk(db=vdisk)

    def get_mounted_vdisk_list(self, vmid):
        vdisk_list = DBVdisk.objects.filter(vm = vmid)
        ret_list = []
        for vdisk in vdisk_list:
            ret_list.append(Vdisk(db=vdisk))
        return ret_list

    def get_mounted_vdisk_count(self, vmid):
        return DBVdisk.objects.filter(vm = vmid).count()