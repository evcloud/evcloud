#coding=utf-8
from django.test import TestCase
from django.contrib.auth.models import User
from compute.models import *
from image.models import *
from storage.models import *
from ..images import get_list, get

from .tools import create_user, create_superuser, create_center, create_group
from .tools import create_ceph_host, create_ceph_image_pool
from .tools import create_xml, create_imagetype, create_image
class ImageTest(TestCase):
    def setUp(self):
        self.u1 = create_user('apiuser')
        self.u2 = create_superuser('superuser')
        
        self.c1 = create_center('测试中心1', '位置1', '备注1')
        self.c2 = create_center('测试中心2', '位置2', '备注2')
        
        self.g1 = create_group(self.c1, '测试集群1', '备注1', [self.u1])
        self.g2 = create_group(self.c1, '测试集群1', '备注2')
        
        self.ch1 = create_ceph_host(self.c1, '0.0.0.0', 6789, '1111111111111')
        self.cp1 = create_ceph_image_pool(self.ch1, 'vmpool')
        
        self.ch2 = create_ceph_host(self.c2, '0.0.0.1', 6789, '222222222222')
        self.cp2 = create_ceph_image_pool(self.ch2, 'vmpool')
        
        it1 = create_imagetype('imagetype1')
        x1 = create_xml('linux', '')

        self.i1 = create_image(self.cp1, x1, it1, 'image1', 'v0.1', 'image@1111')
        self.i2 = create_image(self.cp2, x1, it1, 'image2', 'v0.2', 'image2@2222')

    def test_get_err_args(self):
        req = {'req_user': None}
        exp = {'res': False}
        res = get(req)
        self.assertDictContainsSubset(exp, res)

        req1 = {'req_user': self.u1, 'image_id': -1}
        res1 = get(req1)
        self.assertDictContainsSubset(exp, res1)

        req2 = {'req_user': self.u1}
        res2 = get(req2)
        self.assertDictContainsSubset(exp, res2)

    def test_get_err_perm(self):
        req = {'req_user': self.u1, 'image_id':self.i2.id}
        exp = {'res': False}
        res = get(req)
        self.assertDictContainsSubset(exp, res)

    def test_get_superuser(self):
        req = {'req_user': self.u2, 'image_id': self.i1.id}
        exp = {'res': True, 'info':{
            'id':       self.i1.id,
            'ceph_id':  self.i1.cephpool_id,
            'name':     self.i1.name,
            'version':  self.i1.version,
            'snap':     self.i1.snap,
            'type':     self.i1.type.name,
            'desc':     self.i1.desc
        }}
        res = get(req)
        self.assertDictEqual(exp, res)

        req1 = {'req_user': self.u2, 'image_id': self.i2.id}
        exp1 = {'res': True, 'info':{
            'id':       self.i2.id,
            'ceph_id':  self.i2.cephpool_id,
            'name':     self.i2.name,
            'version':  self.i2.version,
            'snap':     self.i2.snap,
            'type':     self.i2.type.name,
            'desc':     self.i2.desc
        }}
        res1 = get(req1)
        self.assertDictEqual(exp1, res1)

    def test_get(self):
        req = {'req_user': self.u1, 'image_id': self.i1.id}
        exp = {'res': True, 'info':{
            'id':       self.i1.id,
            'ceph_id':  self.i1.cephpool_id,
            'name':     self.i1.name,
            'version':  self.i1.version,
            'snap':     self.i1.snap,
            'type':     self.i1.type.name,
            'desc':     self.i1.desc
        }}
        res = get(req)
        self.assertDictEqual(exp, res)

    def test_get_list_err_args(self):
        req = {'req_user': None, 'ceph_id': self.cp1.id}
        exp = {'res': False}
        res = get_list(req)
        self.assertDictContainsSubset(exp, res)

        req1 = {'req_user': self.u1}
        res1 = get_list(req1)
        self.assertDictContainsSubset(exp, res1)

        req2 = {'req_user': self.u1, 'ceph_id':-1}
        res2 = get_list(req2)
        self.assertDictContainsSubset(exp, res2)

    def test_get_list_err_perm(self):
        req = {'req_user': self.u1, 'ceph_id': self.cp2.id}
        exp = {'res': False}
        res = get_list(req)
        self.assertDictContainsSubset(exp, res)

    def test_get_list_superuser(self):
        req = {'req_user': self.u2, 'ceph_id': self.cp1.id}
        exp = {'res':True, 'list':[
            {
            'id':   self.i1.id,
            'ceph_id': self.i1.cephpool_id,
            'name': self.i1.name,
            'version': self.i1.version,
            'type': self.i1.type.name,
            'order': self.i1.order
            }
        ]}
        res = get_list(req)
        self.assertDictEqual(exp, res)

        req1 = {'req_user': self.u2, 'ceph_id': self.cp2.id}
        exp1 = {'res':True, 'list':[
            {
            'id':   self.i2.id,
            'ceph_id': self.i2.cephpool_id,
            'name': self.i2.name,
            'version': self.i2.version,
            'type': self.i2.type.name,
            'order': self.i2.order
            }
        ]}
        res1 = get_list(req1)
        self.assertDictEqual(exp1, res1)

    def test_get_list(self):
        req = {'req_user': self.u1, 'ceph_id': self.cp1.id}
        exp = {'res':True, 'list':[
            {
            'id':   self.i1.id,
            'ceph_id': self.i1.cephpool_id,
            'name': self.i1.name,
            'version': self.i1.version,
            'type': self.i1.type.name,
            'order': self.i1.order
            }
        ]}
        res = get_list(req)
        self.assertDictEqual(exp, res)
        