#coding=utf-8
from django.test import TestCase
from django.contrib.auth.models import User
from compute.models import *
from network.models import *
from ..net import get_vlan_list, get_vlan, get_vlan_type_list

from .tools import create_user, create_superuser
from .tools import create_center, create_group, create_host
from .tools import create_vlan, create_vlantype

class NetTest(TestCase):
    def setUp(self):
        self.u1 = create_user('apiuser')
        self.u2 = create_superuser('superuser')
        
        self.c1 = create_center('1', '1', '1')
      
        self.g1 = create_group(self.c1, '1', '1', [self.u1])
        self.g2 = create_group(self.c1, '2', '2')
        
        self.vt1 = create_vlantype('vlantype1')
        
        self.v1 = create_vlan('0.0.0.0', 'br1', self.vt1)
        
        self.v2 = create_vlan('0.0.0.1', 'br2', self.vt1, False)
        
        self.h1 = create_host(self.g1, '1.1.1.1', True, [self.v1])
        self.h2 = create_host(self.g2, '1.1.1.2', True, [self.v2])
    
    def test_get_vlan_err_args(self):
        req = {'req_user': 1}
        exp = {'res': False}
        res = get_vlan(req)
        self.assertDictContainsSubset(exp, res)

        req1 = {'req_user': self.u1}
        res1 = get_vlan(req1)
        self.assertDictContainsSubset(exp, res1)

        req2 = {'req_user': self.u1, 'vlan_id': -1}
        res2 = get_vlan(req2)
        self.assertDictContainsSubset(exp, res2)

    def test_get_vlan_err_perm(self):
        req = {'req_user': self.u1, 'vlan_id':self.v2.id}
        exp = {'res': False}
        res = get_vlan(req)
        self.assertDictContainsSubset(exp, res)

    def test_get_vlan_superuser(self):
        req = {'req_user': self.u2, 'vlan_id': self.v1.id}
        exp = {'res': True, 'info':{
                     'id': self.v1.id,
                     'vlan': self.v1.vlan,
                     'br': self.v1.br,
                     'type_code': self.v1.type.code,
                     'type_name': self.v1.type.name,
                     'enable': self.v1.enable}}
        res = get_vlan(req)
        self.assertDictEqual(exp, res)

    def test_get_vlan_superuser1(self):
        req = {'req_user': self.u2, 'vlan_id': self.v2.id}
        exp = {'res': True, 'info':{
                     'id': self.v2.id,
                     'vlan': self.v2.vlan,
                     'br': self.v2.br,
                     'type_code': self.v2.type.code,
                     'type_name': self.v2.type.name,
                     'enable': self.v2.enable}}
        res = get_vlan(req)
        self.assertDictEqual(exp, res)

    def test_get_vlan(self):
        req = {'req_user': self.u1, 'vlan_id': self.v1.id}
        exp = {'res': True, 'info':{
                     'id': self.v1.id,
                     'vlan': self.v1.vlan,
                     'br': self.v1.br,
                     'type_code': self.v1.type.code,
                     'type_name': self.v1.type.name,
                     'enable': self.v1.enable}}
        res = get_vlan(req)
        self.assertDictEqual(exp, res)

    def test_get_vlan_list_err_args(self):
        req = {'req_user': 0}
        exp = {'res': False}
        res = get_vlan_list(req)
        self.assertDictContainsSubset(exp, res)

    def test_get_vlan_list_err_args1(self):
        req = {'req_user': self.u1}
        exp = {'res': False}
        res = get_vlan_list(req)
        self.assertDictContainsSubset(exp, res)

    def test_get_vlan_list_err_args2(self):
        req = {'req_user': self.u1, 'group_id':-1}
        exp = {'res': False}
        res = get_vlan_list(req)
        self.assertDictContainsSubset(exp, res)

    def test_get_vlan_list_err_perm(self):
        req = {'req_user': self.u1, 'group_id': self.g2.id}
        exp = {'res': False}
        res = get_vlan_list(req)
        self.assertDictContainsSubset(exp, res)

    def test_get_vlan_list_superuser(self):
        req = {'req_user': self.u2, 'group_id': self.g1.id}
        exp = {'res': True, 'list':[
            {
                'id': self.v1.id,
                'vlan': self.v1.vlan,
                'br': self.v1.br,
                'type_code': self.v1.type.code,
                'type': self.v1.type.name,
                'enable': self.v1.enable,
                'order': self.v1.order
            }
        ]}
        res = get_vlan_list(req)
        self.assertDictEqual(exp, res)
    
    def test_get_vlan_list_superuser1(self):
        req = {'req_user': self.u2, 'group_id': self.g2.id}
        exp = {'res': True, 'list':[
            {
                'id': self.v2.id,
                'vlan': self.v2.vlan,
                'br': self.v2.br,
                'type_code': self.v2.type.code,
                'type': self.v2.type.name,
                'enable': self.v2.enable,
                'order': self.v2.order
            }
        ]}
        res = get_vlan_list(req)
        self.assertDictEqual(exp, res)

    def test_get_vlan_list(self):
        req = {'req_user': self.u1, 'group_id': self.g1.id}
        exp = {'res': True, 'list':[
            {
                'id': self.v1.id,
                'vlan': self.v1.vlan,
                'br': self.v1.br,
                'type_code': self.v1.type.code,
                'type': self.v1.type.name,
                'enable': self.v1.enable,
                'order': self.v1.order
            }
        ]}
        res = get_vlan_list(req)
        self.assertDictEqual(exp, res)

    def test_get_vlan_type_list_err_args(self):
        req = {'req_user': 0}
        exp = {'res': False}
        res = get_vlan_type_list(req)
        self.assertDictContainsSubset(exp, res)

    def test_get_vlan_type_list(self):
        req = {'req_user': self.u1}
        exp = {'res': True, 'list':[
            {
                'code': self.vt1.code,
                'name': self.vt1.name,
                'order': self.vt1.order
            }
        ]}
        res = get_vlan_type_list(req)
        self.assertDictEqual(exp, res)
        

        