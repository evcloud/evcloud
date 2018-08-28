#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2015-10-16
#@desc:    分中心相关的API函数，每一个函数封装并实现一个API接口的功能。
########################################################################


from compute.api import CenterAPI

from .tools import catch_error
from .tools import api_log

@api_log
@catch_error
def get_list(args=None):
    '''获取分中心列表'''
    api = CenterAPI()
    center_list = api.get_center_list_in_perm(args['req_user'])
        
    ret_list = []
    for center in center_list:       
        ret_list.append({
            'id':   center.id,
            'name': center.name,
            'location': center.location,
            'desc': center.desc,
            'order': center.order})
    return {'res': True, 'list': ret_list}