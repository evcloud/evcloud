#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2015-10-16
#@desc:    镜像相关的API函数，每一个函数封装并实现一个API接口的功能。
########################################################################

from .tools import args_required, catch_error, api_log
from .error import ERR_AUTH_PERM, ERR_IMAGE_ID, ERR_CEPH_ID

from image import get_image, get_images, get_image_types
from storage.ceph import get_cephpool 

@api_log
@catch_error
@args_required('image_id')
def get(args):
    '''获取镜像信息'''
    info = {}
    image = get_image(args['image_id'])
    if not image:
        return {'res': False, 'err': ERR_IMAGE_ID}
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

# @api_log
# @catch_error
@args_required('ceph_id')
def get_list(args):
    '''获取镜像列表'''
    ret_list = []
    cephpool = get_cephpool(args['ceph_id'])
    if not cephpool:
        return {'res': False, 'err': ERR_CEPH_ID}
    if not cephpool.managed_by(args['req_user']):
        return {'res': False, 'err': ERR_AUTH_PERM}
    
    image_list = get_images(args['ceph_id'])
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
    ret_list = get_image_types()
    return {'res': True, 'list': ret_list}