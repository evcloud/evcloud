#coding=utf-8
from .models import Image as DBImage
from .models import ImageType
from .models import DiskSnap as DBDiskSnap
from .image import Image
from .snap import DiskSnap
from datetime import datetime
from django.conf import settings

from api.error import ERR_IMAGE_ID, ERR_DISK_NAME, Error,ERR_DISKSNAP_ID

class ImageManager(object):
    error = ''

    def get_image_by_id(self, image_id):
        image = DBImage.objects.filter(id = image_id)
        if not image.exists():
            raise Error(ERR_IMAGE_ID)
        return Image(image[0])

    def get_image_list_by_pool_id(self, pool_id, enable=None):
        image_list = DBImage.objects.filter(cephpool_id = pool_id)
        if enable == True:
            print(image_list)
            a = image_list
            image_list = image_list.filter(enable=True)
            b = image_list
            print(set(a).difference(b))
        elif enable == False:
            image_list = image_list.filter(enable=False)
        image_list = image_list.order_by('order')
        ret_list = []
        for image in image_list:
            ret_list.append(Image(image))
        return ret_list

    def get_image_type_list(self):
        types = ImageType.objects.all().order_by('order')
        ret_list = []
        for t in types:
            ret_list.append({
                'code': t.code,
                'name': t.name,
                'order': t.order
                })
        return ret_list

            
    def get_image_info(self, image):
        if type(image) != Image:
            image = DBImage.objects.filter(pk = image)
            if not image:
                raise Error(ERR_IMAGE_ID)
            image = image[0]
        try:
            return {
                'image_snap': image.snap,
                'image_name': image.fullname,
                'image_version': image.version,
                'ceph_id': image.cephpool_id,
                'ceph_host': image.cephpool.host.host,
                'ceph_port': image.cephpool.host.port,
                'ceph_uuid': image.cephpool.host.uuid,
                'ceph_pool': image.cephpool.pool,
                'ceph_username': image.cephpool.host.username,
                'ceph_hosts_xml': image.cephpool.host.hosts_xml
            }
        except:
            return False
        

    def get_xml_tpl(self,image_id):
        image = DBImage.objects.filter(pk = image_id)
        if not image:
            self.error = 'Image (%s) not exist.' % image_id
            return False
        image = image[0]
        return image.xml.xml


    def create_disk_snap_db(self,cephpool_id,disk,snap,image_id,vm_uuid,remarks=None):
        obj = DBDiskSnap()
        obj.cephpool_id = cephpool_id
        obj.disk = disk
        obj.snap = snap
        obj.image_id = image_id
        obj.vm_uuid = vm_uuid
        obj.remarks = remarks
        obj.save()
        return DiskSnap(obj)

    def get_disk_snap_by_id(self, disk, snap_id):
        objs = DBDiskSnap.objects.filter(id = snap_id,disk=disk)
        if not objs.exists():
            raise Error(ERR_DISKSNAP_ID)
        return DiskSnap(objs[0])

    def get_disk_snap_list_by_disk(self, disk):
        objs = DBDiskSnap.objects.filter(disk = disk).order_by("-create_time")
        ret_list = [DiskSnap(obj) for obj in objs]
        return ret_list

    def batch_update_disk_of_disk_snap(self,old_disk,new_disk):
        '''磁盘归档时批量更新磁盘名称'''
        try:
            objs = DBDiskSnap.objects.filter(disk = old_disk)
            if objs.exists():
                objs.update(disk=new_disk)        
            return True  
        except Exception as e:
            if settings.DEBUG: raise e 
            return False

    def batch_delete_disk_snap_db_by_disk(self,disk):
        try:
            objs = DBDiskSnap.objects.filter(disk = disk)
            if objs.exists():
                objs.delete() 
            return True  
        except Exception as e:
            if settings.DEBUG: raise e 
            return False

    