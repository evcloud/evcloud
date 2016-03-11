#coding=utf-8
import uuid
from .models import DBCephVolume
from api.error import Error
from api.error import ERR_VOLUME_CREATE_DB
from api.error import ERR_VOLUME_ID
from api.error import ERR_CEPH_CREATE
from .volume import CephVolume

class CephManager(object):
    def create_volume(self, cephpool, size, group_id, volume_id=None):
        if not volume_id:
            volume_id = str(uuid.uuid4())
        create_success = cephpool.create(volume_id, size)
        if create_success:
            try:
                db = DBCephVolume()
                db.uuid = volume_id
                db.size = size
                db.cephpool_id = cephpool.id
                db.group_id = group_id
                db.save()        
            except Exception as e:
                cephpool.rm(volume_id)
                raise Error(ERR_VOLUME_CREATE_DB)
            else:
                return volume_id
        else:
            raise Error(ERR_CEPH_CREATE)

    def get_volume_list(self, user_id=None, creator=None, cephpool_id=None, group_id=None, vm_uuid=None):
        volume_list = DBCephVolume.objects.all().order_by('-create_time')
        if user_id:
            volume_list = volume_list.filter(user_id=user_id)
        if creator:
            volume_list = volume_list.filter(creator=creator)
        if cephpool_id:
            volume_list = volume_list.filter(cephpool_id=cephpool_id)
        if group_id:
            volume_list = volume_list.filter(group_id=group_id)
        if vm_uuid:
            volume_list = volume_list.filter(vm=vm_uuid)
        ret_list = []
        for volume in volume_list:
            ret_list.append(CephVolume(db=volume))
        return ret_list

    def get_volume_quota_by_group_id(self, group_id):
        return 0

    def get_group_quota_by_group_id(self, group_id):
        return 0

    def set_volume_quota(self, size):
        '''目前使用Django admin模块维护数据，暂不使用此函数'''
        return False

    def set_group_quota(self, size):
        '''目前使用Django admin模块维护数据，暂不使用此函数'''
        return False

    def get_volume_by_id(self, volume_id):
        try:
            volume = DBCephVolume.objects.get(uuid = volume_id)
        except:
            raise Error(ERR_VOLUME_ID)
        return CephVolume(db=volume)

    def get_mounted_volume_list(self, vmid):
        volume_list = DBCephVolume.objects.filter(vm = vmid)
        ret_list = []
        for volume in volume_list:
            ret_list.append(CephVolume(db=volume))
        return ret_list

    def get_mounted_volume_count(self, vmid):
        return DBCephVolume.objects.filter(vm = vmid).count()