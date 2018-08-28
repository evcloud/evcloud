#coding=utf-8
from django.test import TestCase
from django.contrib.auth.models import User
from compute.models import *
from ..host import get_list, get

from .tools import create_user, create_superuser, create_center, create_group
from .tools import create_host

class HostTest(TestCase):
    def setUp(self):
        self.u1 = create_user('apiuser')
        self.u2 = create_superuser('superuser')
        
        self.c1 = create_center('测试中心1', '位置1', '备注1')
        self.c2 = create_center('测试中心2', '位置2', '备注2')
        
        self.g1 = create_group(self.c1, '测试集群1', '备注11', [self.u1])
        self.g2 = create_group(self.c1, '测试集群2', '备注')
        
        self.h1 = create_host(self.g1, '1.1.1.1')
        self.h2 = create_host(self.g2, '1.1.1.2')
        
    def test_get_err_args(self):
        req = {'req_user': self.u1}
        exp = {'res': False}
        res = get(req)
        self.assertDictContainsSubset(exp, res)

        req1 = {'req_user': self.u1, 'host_id': -1}
        res1 = get(req1)
        self.assertDictContainsSubset(exp, res1)

    def test_get_err_perm(self):
        req = {'req_user': self.u1, 'host_id': self.h2.id}
        exp = {'res': False}
        res = get(req)
        self.assertDictContainsSubset(exp, res)

    def test_get_superuser(self):
        req = {'req_user': self.u2, 'host_id': self.h2.id}
        exp = {'res': True, 
                'info':{
                     'id': self.h2.id,
                     'group_id': self.h2.group_id,
                     'vlan_list': [vlan.vlan for vlan in self.h2.vlan.all()],
                     'ipv4': self.h2.ipv4,
                     'vcpu_total': self.h2.vcpu_total,
                     'vcpu_allocated': self.h2.vcpu_allocated,
                     'mem_total': self.h2.mem_total,
                     'mem_allocated': self.h2.mem_allocated,
                     'mem_reserved': self.h2.mem_reserved,
                     'vm_limit': self.h2.vm_limit,
                     'vm_created': self.h2.vm_created,
                     'enable': self.h2.enable
                     }
        }
        res = get(req)
        self.assertDictEqual(exp, res)

    def test_get(self):
        req = {'req_user': self.u1, 'host_id': self.h1.id}
        exp = {'res': True, 
                'info':{
                     'id': self.h1.id,
                     'group_id': self.h1.group_id,
                     'vlan_list': [vlan.vlan for vlan in self.h1.vlan.all()],
                     'ipv4': self.h1.ipv4,
                     'vcpu_total': self.h1.vcpu_total,
                     'vcpu_allocated': self.h1.vcpu_allocated,
                     'mem_total': self.h1.mem_total,
                     'mem_allocated': self.h1.mem_allocated,
                     'mem_reserved': self.h1.mem_reserved,
                     'vm_limit': self.h1.vm_limit,
                     'vm_created': self.h1.vm_created,
                     'enable': self.h1.enable
                     }
        }
        res = get(req)
        self.assertDictEqual(exp, res)

    def test_get_list_err_args(self):
        req = {'req_user': self.u1}
        exp = {'res': False}
        res = get_list(req)
        self.assertDictContainsSubset(exp, res)

        req1 = {'req_user': self.u1, 'group_id': -1}
        res1 = get_list(req1)
        self.assertDictContainsSubset(exp, res1)
    
    def test_get_list_err_perm(self):
        req = {'req_user': self.u1, 'group_id': self.g2.id}
        exp = {'res': False}
        res = get_list(req)
        self.assertDictContainsSubset(exp, res)

    def test_get_list_superuser(self):
        req = {'req_user': self.u2, 'group_id': self.g2.id}
        exp = {'res':True, 'list':[
            {
            'id':   self.h2.id,
            'group_id': self.h2.group_id,
            'ipv4': self.h2.ipv4,
            'vcpu_total': self.h2.vcpu_total,
            'vcpu_allocated': self.h2.vcpu_allocated,
            'mem_total': self.h2.mem_total,
            'mem_allocated': self.h2.mem_allocated,
            'mem_reserved': self.h2.mem_reserved,
            'vm_limit': self.h2.vm_limit,
            'vm_created': self.h2.vm_created,
            'enable': self.h2.enable,
            'net_types':[vlan.type.name for vlan in self.h2.vlan.all()]}
        ]}
        res = get_list(req)
        self.assertDictEqual(exp, res)

    def test_get_list(self):
        req = {'req_user': self.u1, 'group_id': self.g1.id}
        exp = {'res': True, 'list':[
            {
            'id':   self.h1.id,
            'group_id': self.h1.group_id,
            'ipv4': self.h1.ipv4,
            'vcpu_total': self.h1.vcpu_total,
            'vcpu_allocated': self.h1.vcpu_allocated,
            'mem_total': self.h1.mem_total,
            'mem_allocated': self.h1.mem_allocated,
            'mem_reserved': self.h1.mem_reserved,
            'vm_limit': self.h1.vm_limit,
            'vm_created': self.h1.vm_created,
            'enable': self.h1.enable,
            'net_types':[vlan.type.name for vlan in self.h1.vlan.all()]}
        ]}
        res = get_list(req)
        self.assertDictEqual(exp, res)

        
        