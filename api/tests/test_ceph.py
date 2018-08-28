#coding=utf-8
from django.test import TestCase
from django.contrib.auth.models import User
from compute.models import *
from storage.models import *
from ..ceph import get_list, get

from .tools import create_user, create_superuser, create_group, create_center, create_ceph_host, create_ceph_image_pool

class CephTest(TestCase):
    def setUp(self):
        self.u1 = create_user('apiuser')
        self.u2 = create_superuser('superuser')

        self.c1 = create_center('testcenter1', 'location1', 'desc1')
        self.c2 = create_center('testcenter2', 'location2', 'desc2')
        
        self.g1 = create_group(self.c1, 'group1', 'desc1', [self.u1])
        
        self.ch1 = create_ceph_host(self.c1, '0.0.0.0', 6789, '111111111111111')
        self.cp1 = create_ceph_image_pool(self.ch1, 'vmpool')
        self.ch2 = create_ceph_host(self.c2, '0.0.0.1', 6789, '22222222222222222')
        self.cp2 = create_ceph_image_pool(self.ch2, 'vmpool')    

    def test_get_no_user(self):

        #user有误
        req1 = {'req_user': None}  
        res1 = get(req1)
        exp1 = {'res':False}
        self.assertDictContainsSubset(exp1,res1)

    def test_get_no_cephpoolid(self):
        #缺少参数 cephpoolid
        req2 = {'req_user': self.u1}
        exp2 = {'res': False}
        res2 = get(req2)
        self.assertDictContainsSubset(exp2, res2)
        
    def test_get_err_cephpoolid(self):
        #参数cephpoolid错误
        req3 = {'req_user': self.u1, 'cephpool_id': -11}
        exp3 = {'res': False}
        res3 = get(req3)
        self.assertDictContainsSubset(exp3, res3)

    def test_get_err_perm(self):
        #越权获取
        req4 = {'req_user': self.u1, 'cephpool_id': self.cp2.id}
        exp4 = {'res': False}
        res4 = get(req4)
        self.assertDictContainsSubset(exp4, res4)
          
    def test_get(self):
        #正常获取
        req5 = {'req_user': self.u1, 'cephpool_id': self.cp1.id}
        exp5 = {'res': True,'info':{
                'id':   self.cp1.id,
                'pool': self.cp1.pool,
                'type': self.cp1.type,
                'center_id': self.cp1.host.center_id,
                'host': self.cp1.host.host,
                'port': self.cp1.host.port,
                'uuid': self.cp1.host.uuid
                }}
        res5 = get(req5)
        self.assertDictEqual(exp5, res5)

    def test_get_list_no_user(self):
        #user参错误
        req1 = {'req_user': None, 'center_id': self.c1.id}
        exp1 = {'res': False}
        res1 = get_list(req1)
        self.assertDictContainsSubset(exp1, res1)

    def test_get_list_err_centerid(self):
        #center_id 参数错误
        req2 = {'req_user': self.u1, 'center_id': -1}
        exp2 = {'res': False}
        res2 = get_list(req2)
        self.assertDictContainsSubset(exp2, res2)

    def test_get_list_err_perm(self):
        #获取权限外的数据
        req3 = {'req_user': self.u1, 'center_id':self.c2.id}
        exp3 = {'res': False}
        res3 = get_list(req3)
        self.assertDictContainsSubset(exp3, res3)

    def test_get_list(self):
        #获取权限内的数据
        req4 = {'req_user': self.u1, 'center_id': self.c1.id}
        req4_1 = {'req_user': self.u2, 'center_id': self.c1.id}
        exp4 = {'res': True, 'list':[{
            'id':   self.cp1.id,
            'pool': self.cp1.pool,
            'type': self.cp1.type,
            'center_id': self.cp1.host.center_id,
            'host': self.cp1.host.host,
            'port': self.cp1.host.port,
            'uuid': self.cp1.host.uuid
            }]}
        res4 = get_list(req4)
        res4_1 = get_list(req4_1)
        self.assertDictEqual(exp4, res4)
        self.assertDictEqual(exp4, res4_1)
