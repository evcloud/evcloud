#coding=utf-8
from django.contrib.auth.models import User

from api.error import (ERR_DISK_INIT, ERR_DISK_ARCHIVE, ERR_CEPH_ID,
                       ERR_IMAGE_INFO, ERR_IMAGE_CEPHHOST, ERR_IMAGE_CEPHPOOL) 
from api.error import Error
from compute.group import has_center_perm
from storage.ceph import get_cephpool

from .manager import ImageManager
from .models import Image as ModelImage
from .models import ImageType


imagemanager = ImageManager()

def init_disk(image_id, disk_name):
    '''初始化磁盘'''
    res = imagemanager.init_disk(image_id, disk_name)
    if not res:
        raise Error(ERR_DISK_INIT)
    return True, ''

def archive_disk(cephpool_id, disk_name, archive_disk_name=None):
    res = imagemanager.archive_disk(cephpool_id, disk_name, archive_disk_name)
    if res == False:
        return False, ERR_DISK_ARCHIVE
    return True, res

def get_image_info(image_id):
    '''根据镜像ID获取镜像相关的信息， 返回数据格式： {
                'image_snap': *******,
                'image_name': *******,
                'ceph_host': *.*.*.*,
                'ceph_port': ****,
                'ceph_uuid': ************************,
                'ceph_pool': ******
            }
    '''
    res = imagemanager.get_image_info(image_id)
    if not res:
        return False, ERR_IMAGE_INFO
    return True, res


def get_image(image_id):
    image = ModelImage.objects.filter(id = image_id)
    if not image.exists():
        return False
    return Image(image[0])

def get_images(pool_id):
    images = ModelImage.objects.filter(cephpool_id = pool_id).order_by('order')
    ret_list = []
    for image in images:
        ret_list.append(Image(image))
    return ret_list

def get_image_types():
    types = ImageType.objects.all().order_by('order')
    ret_list = []
    for t in types:
        ret_list.append({
            'code': t.code,
            'name': t.name,
            'order': t.order
            })
    return ret_list
    
class Image(object):
    def __init__(self, obj):
        self.db_obj = obj        
        if type(obj) == ModelImage:
            self.db_obj = obj
        else:
            raise RuntimeError('Image init error.')
        
        self.xml = self.db_obj.xml.xml
        self.type_code = self.db_obj.type.code
        self.type_name = self.db_obj.type.name
        
    def __getattr__(self, name):
        return self.db_obj.__getattribute__(name)
    
    def managed_by(self, user):
        if type(user) != User:
            raise RuntimeError('user type error.')
        if user.is_superuser:
            return True
        return has_center_perm(user, self.db_obj.cephpool.host.center.id)

