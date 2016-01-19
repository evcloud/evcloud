#coding=utf-8
from .models import Image
from datetime import datetime
from storage.ceph import get_cephpool
from django.conf import settings

from api.error import ERR_IMAGE_ID, ERR_DISK_NAME, Error

class ImageManager(object):
    error = ''

    def init_disk(self, image_id, diskname):
        image = Image.objects.filter(pk = image_id)
        if not image:
            raise Error(ERR_IMAGE_ID)
        try:
            diskname = str(diskname)
        except:
            raise Error(ERR_DISK_NAME)
        if len(diskname) <= 0:
            raise Error(ERR_DISK_NAME)

        image = image[0]
        cephpool = get_cephpool(image.cephpool_id)
        res  = cephpool.clone(image.snap, str(diskname))
        if res:
            return True
        else:
            return False
            
    def get_image_info(self, image):
        if type(image) != Image:
            image = Image.objects.filter(pk = image)
            if not image:
                raise Error(ERR_IMAGE_ID)
            image = image[0]
        try:
            return {
                'image_snap': image.snap,
                'image_name': image.fullname,
                'ceph_host': image.cephpool.host.host,
                'ceph_port': image.cephpool.host.port,
                'ceph_uuid': image.cephpool.host.uuid,
                'ceph_pool': image.cephpool.pool
            }
        except:
            return False
        
    def rm_disk(self, image_id, diskname):
        image = Image.objects.filter(pk = image_id)
        if not image:
            raise Error(ERR_IMAGE_ID)
        image = image[0]
        cephpool = get_cephpool(image.cephpool_id)
        res = cephpool.rm(str(diskname))
        if not res:
            self.error = cephpool.error
        return res
        
    def archive_disk(self, cephpool_id, disk_name, archive_disk_name = None):
        if settings.DEBUG: print('[iamge.manager.archive disk]', cephpool_id, disk_name, archive_disk_name)
        cephpool = get_cephpool(cephpool_id)
        if not cephpool.exists(disk_name):
            if settings.DEBUG: print('[iamge.manager.archive disk]', '目标镜像未找到，无需归档操作')
            return archive_disk_name
        if archive_disk_name == None:
            archive_disk_name = 'x_'+str(disk_name)+'_'+datetime.now().strftime("%Y%m%d%H%M%S%f")
        else:
            try:
                archive_disk_name = str(archive_disk_name)
            except:
                raise Error(ERR_DISK_NAME)
            if len(archive_disk_name) <= 0:
                raise Error(ERR_DISK_NAME)
            
        res = cephpool.mv(disk_name, archive_disk_name)
        if not res:
            if settings.DEBUG: print('[iamge.manager.archive disk]', 'ceph mv操作失败', cephpool.error)
            self.error = cephpool.error
            return False
        if settings.DEBUG: print('[iamge.manager.archive disk]', '镜像归档成功', archive_disk_name)
        return archive_disk_name

    def get_xml_tpl(self,image_id):
        image = Image.objects.filter(pk = image_id)
        if not image:
            self.error = 'Image (%s) not exist.' % image_id
            return False
        image = image[0]
        return image.xml.xml

    

    
    