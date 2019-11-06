#coding=utf-8
import uuid

from django.db import transaction
from django.utils import timezone

from vms.models import Vm
from .models import Vdisk
from .models import Quota

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

class VdiskManager:
    '''
    虚拟硬盘管理器
    '''
    def get_vdisk_by_uuid(self, uuid:str):
        '''
        通过uuid获取虚拟机元数据

        :param uuid: 虚拟机uuid hex字符串
        :return:
            Vdisk() or None     # success

        :raise:  VdiskError
        '''
        try:
            return Vdisk.objects.filter(uuid=uuid).first()
        except Exception as e:
            raise VdiskError(msg=str(e))

    def create_vdisk(self, quota, size:int, user):
        '''
        创建一个虚拟云硬盘

        :param quota: 硬盘所属的云硬盘CEPH存储池对象或id
        :param size: 硬盘的容量大小
        :param user: 创建硬盘的用户
        :return:
            Vdisk()     # success

        :raises: VdiskError
        '''
        if size <= 0:
            raise VdiskError(msg='创建的硬盘大小必须大于0')

        if isinstance(quota, int):
            quota = Quota.objects.filter(id=quota).first()

        if not isinstance(quota, Quota):
            raise VdiskError(msg='无效的quota或quota id')

        if not quota.check_disk_size_limit(size=size):
            raise VdiskError(msg='超出了可创建硬盘最大容量')

        if not quota.meet_needs(size=size):
            raise VdiskError(msg='没有足够的存储容量创建硬盘')

        # 向硬盘CEPH存储池申请容量
        if not quota.claim(size=size):
            raise VdiskError(msg='申请硬盘存储容量失败')

        vd = Vdisk(size=size, quota=quota, user=user)
        try:
            vd.save() # save内会创建元数据和ceph rbd image
        except Exception as e:
            raise VdiskError(msg=str(e))

        return vd

    def mount_to_vm(self, vdisk_uuid:str, vm_uuid:str, dev):
        '''
        标记虚拟硬盘挂载到虚拟机,只是在硬盘元数据层面和虚拟机建立挂载关系

        :param vdisk_uuid: 虚拟硬盘uuid
        :param vm_uuid: 虚拟机uuid
        :param dev:
        :return:
            True

        :raises: VdiskError
        '''
        try:
            with transaction.atomic():
                disk = Vdisk.objects.select_for_update().get(pk=vdisk_uuid)
                # 硬盘已被挂载
                if disk.vm:
                    # 已挂载到此虚拟机
                    if disk.vm == vdisk_uuid:
                        return True

                    # 检查硬盘挂载的虚拟机是否存在
                    if Vm.objects.filter(pk=disk.vm).exists():
                        raise VdiskError(msg='硬盘已被挂载到其他虚拟机')
                # 挂载
                if disk.enable == True:
                    disk.vm = vm_uuid
                    disk.attach_time = timezone.now()
                    disk.dev = dev
                    try:
                        disk.save(update_fields=['vm', 'dev', 'attach_time'])
                    except Exception:
                        raise VdiskError(msg='更新元数据失败')
                else:
                    raise VdiskError(msg='硬盘已暂停使用')
        except Vdisk.DoesNotExist as e:
            raise VdiskError(msg='硬盘不存在')
        return True

    def umount_from_vm(self, vdisk_uuid:str):
        '''
        从虚拟机卸载虚拟硬盘,只是在硬盘元数据层面和虚拟机解除挂载关系

        :param vdisk_uuid: 虚拟硬盘uuid
        :return:
            True

        :raises: VdiskError
        '''
        try:
            with transaction.atomic():
                disk = Vdisk.objects.select_for_update().get(pk=vdisk_uuid)
                # 硬盘未挂载
                if not disk.vm:
                    return True

                # 卸载
                disk.vm = ''
                disk.dev = ''
                try:
                    disk.save(update_fields=['vm', 'dev'])
                except Exception:
                    raise VdiskError(msg='更新元数据失败')
        except Vdisk.DoesNotExist as e:
            raise VdiskError(msg='硬盘不存在')
        return True

    def get_vm_vdisk_queryset(self, vm_uuid:str):
        '''
        获取挂载到制定虚拟机下的所有虚拟硬盘查询集

        :param vm_uuid: 虚拟机uuid
        :return:
            QuerySet()
        '''
        return Vdisk.objects.filter(vm=vm_uuid).all()

    def get_mounted_vdisk_count(self, vm_uuid:str):
        '''
        获取虚拟机下已挂载虚拟硬盘的数量

        :param vm_uuid: 虚拟机uuid
        :return:
            int
        '''
        qs = self.get_vm_vdisk_queryset(vm_uuid=vm_uuid)
        return qs.count()

    def get_vdisk_list(self, user_id=None, creator=None, cephpool_id=None, group_id=None, vm_uuid=None):
        vdisk_list = Vdisk.objects.all().order_by('-create_time')
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
            ret_list.append(vdisk)
        return ret_list
