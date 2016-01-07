#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2015-10-16
#@desc:    分中心相关的API函数，每一个函数封装并实现一个API接口的功能。
########################################################################

from compute.center import get_centers
from .tools import catch_error, print_process_time, api_log

@api_log
@catch_error
def get_list(args=None):
    '''获取分中心列表'''
    
    if args['req_user'].is_superuser:
        center_list = get_centers()
    else:
        center_list = get_centers()
        def do_filter(c):
            if c.managed_by(args['req_user']):
                return c
        center_list = filter(do_filter, center_list)
        
    ret_list = []
    for center in center_list:       
        ret_list.append({
            'id':   center.id,
            'name': center.name,
            'location': center.location,
            'desc': center.desc})
    return {'res': True, 'list': ret_list}