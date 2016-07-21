#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2015-10-16
#@desc:    镜像相关的API函数，每一个函数封装并实现一个API接口的功能。
########################################################################

from .tools import args_required
from .tools import catch_error
from .tools import api_log
from .error import ERR_AUTH_PERM

from image.api import ImageAPI
from storage.api import CephStorageAPI

@api_log
@catch_error
@args_required('image_id')
def get(args):
    '''获取镜像信息'''
    info = {}
    image_api = ImageAPI()
    image = image_api.get_image_by_id(args['image_id'])
    
    if not image.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
    
    info = {
        'id':       image.id,
        'ceph_id':  image.cephpool_id,
        'name':     image.name,
        'version':  image.version,
        'snap':     image.snap,
        'type':     image.type_name,
        'desc':     image.desc
    }
    return {'res': True, 'info': info}    

@api_log
@catch_error
@args_required('ceph_id')
def get_list(args):
    '''获取镜像列表'''
    ret_list = []
    storage_api = CephStorageAPI()
    image_api = ImageAPI()
    cephpool = storage_api.get_pool_by_id(args['ceph_id'])

    if not cephpool.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
    if 'enable' in args:
        enable = args['enable']
    else:
        enable = None
    image_list = image_api.get_image_list_by_pool_id(args['ceph_id'], enable)
    for image in image_list:
        ret_list.append({
            'id':   image.id,
            'ceph_id': image.cephpool_id,
            'name': image.name,
            'version': image.version,
            'type': image.type_name,
            'order': image.order
            })
    return {'res': True, 'list': ret_list}

# @api_log
# @catch_error
def get_type_list(args=None):
    image_api = ImageAPI()
    ret_list = image_api.get_image_type_list()
    return {'res': True, 'list': ret_list}