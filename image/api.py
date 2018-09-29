#coding=utf-8
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User

from api.error import Error
from api.error import ERR_DISK_INIT
from api.error import ERR_DISK_ARCHIVE
from api.error import ERR_CEPH_ID
from api.error import ERR_IMAGE_INFO
from api.error import ERR_IMAGE_CEPHHOST
from api.error import ERR_IMAGE_CEPHPOOL

from storage.api import StorageAPI

from .manager import ImageManager




class ImageAPI(object):
    def __init__(self, manager=None, storage_api=None):
        if manager:
            self.manager = manager
        else:
            self.manager = ImageManager()
        if storage_api:
            self.storage_api = storage_api
        else:
            self.storage_api = StorageAPI()        

    def _valid_diskname(self, disk_name):
        try:
            disk_name = str(disk_name)
        except:
            return False
        if len(disk_name) <= 0:
            return False
        return True

    def init_disk(self, image_id, disk_name):
        '''初始化磁盘'''
        image = self.manager.get_image_by_id(image_id)
        if not self._valid_diskname(disk_name):
            raise Error(ERR_DISK_NAME)
        return self.storage_api.clone(image.cephpool_id, image.snap, disk_name)

    def rm_disk(self, image_id, disk_name):
        image = self.manager.get_image_by_id(image_id)
        if not self._valid_diskname(disk_name):
            raise Error(ERR_DISK_NAME)
        if self.storage_api.rm(image.cephpool_id, disk_name):
            return self._batch_delete_snaps_db_by_disk_name(disk_name)
        return False

    def archive_disk(self, image_id, disk_name, archive_disk_name=None,cephpool_id=None):
        if archive_disk_name == None:
            archive_disk_name = 'x_'+datetime.now().strftime("%Y%m%d%H%M%S")+'_'+str(disk_name)
            #archive_disk_name = 'x_'+datetime.now().strftime("%Y%m%d%H%M%S%f")+'_'+str(disk_name)
        else:
            if not self._valid_diskname(disk_name):
                raise Error(ERR_DISK_NAME)
        if not cephpool_id:
            image = self.manager.get_image_by_id(image_id)
            cephpool_id = image.cephpool_id
        if self.storage_api.mv(cephpool_id, disk_name, archive_disk_name):
            self._batch_update_disk_of_disk_snap(disk_name,archive_disk_name)
            return archive_disk_name
        return False

    def disk_exists(self, image_id, disk_name,cephpool_id=None):
        if not cephpool_id:
            image = self.manager.get_image_by_id(image_id)
            cephpool_id = image.cephpool_id
        return self.storage_api.exists(cephpool_id, disk_name)

    def restore_disk(self, image_id, archive_disk_name,disk_name=None):
        try:
            if not disk_name:
                disk_name = archive_disk_name[17:]
        except:
            raise Error(ERR_DISK_NAME)
        if not self._valid_diskname(disk_name):
            raise Error(ERR_DISK_NAME)
        image = self.manager.get_image_by_id(image_id)
        if self.storage_api.mv(image.cephpool_id, archive_disk_name, disk_name):
            self._batch_update_disk_of_disk_snap(archive_disk_name,disk_name)
            return True
        return False        

    def get_image_info_by_id(self, image_id):
        '''根据镜像ID获取镜像相关的信息， 返回数据格式： {
                    'image_snap': *******,
                    'image_name': *******,
                    'image_version': ***,
                    'ceph_id': *,
                    'ceph_host': *.*.*.*,
                    'ceph_port': ****,
                    'ceph_uuid': ************************,
                    'ceph_pool': ******,
                    'ceph_username': *****

                }
        '''
        res = self.manager.get_image_info(image_id)
        if not res:
            raise Error(ERR_IMAGE_INFO)
        return res

    def get_xml_tpl(self, image_id):
        image = self.manager.get_image_by_id(image_id)
        return image.xml

    def get_image_by_id(self, image_id):
        return self.manager.get_image_by_id(image_id)

    def get_image_list_by_pool_id(self, pool_id, enable=None):
        return self.manager.get_image_list_by_pool_id(pool_id, enable)

    def get_image_type_list(self):
        return self.manager.get_image_type_list()


    def create_disk_snap(self,cephpool_id,disk,image_id,vm_uuid,remarks=None):
        if not self.disk_exists(image_id,disk,cephpool_id=cephpool_id):
            if settings.DEBUG: print('[create_disk_snap]', '磁盘不存在',disk)
            return None
        snap = datetime.now().strftime("%Y%m%d%H%M%S")
        fullname = "%s@%s" %(disk,snap)
        if self.storage_api.create_snap(cephpool_id, fullname):                  
            snap_obj= self.manager.create_disk_snap_db(cephpool_id,disk,snap,image_id,vm_uuid,remarks=remarks)            
            if settings.DEBUG: print('[create_disk_snap]', '快照创建成功') 
            return snap_obj
        if settings.DEBUG: print('[create_disk_snap]', '快照创建失败') 
        return None

    def get_disk_snap_list_by_disk(self, disk):
        if self._valid_diskname(disk):
            return self.manager.get_disk_snap_list_by_disk(disk)
        return []

    def get_disk_snap_by_id(self,disk,snap_id):
        return self.manager.get_disk_snap_by_id(disk,snap_id)

    def rollback_disk_snap(self,disk,snap_id):
        disk_snap = self.get_disk_snap_by_id(disk,snap_id)
        res = self.storage_api.rollback_snap(disk_snap.cephpool_id, disk_snap.fullname)
        return res

    def _batch_update_disk_of_disk_snap(self,old_disk_name,new_disk_name):
        """批量更新指定disk的快照的disk""" 
        if self._valid_diskname(new_disk_name):
            return self.manager.batch_update_disk_of_disk_snap(old_disk_name,new_disk_name)            
        return False

    def _batch_delete_snaps_db_by_disk_name(self,disk):
        """批量删除指定disk的快照记录"""
        if self._valid_diskname(disk):
            return self.manager.batch_delete_disk_snap_db_by_disk(disk)            
        return False

    def delete_disk_snap_by_id(self,disk,snap_id):
        disk_snap = self.get_disk_snap_by_id(disk,snap_id)        
        try:
            if self.storage_api.rm_snap(disk_snap.cephpool_id, disk_snap.fullname):
                disk_snap.delete()
                return True
        except Exception as e:
            print(e)
        return False

    def set_disk_snap_remarks(self,disk,snap_id,remarks):
        disk_snap = self.get_disk_snap_by_id(disk,snap_id)
        if disk_snap.set_remarks(remarks):
            return True
        return False
