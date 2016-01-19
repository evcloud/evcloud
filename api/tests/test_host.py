#coding=utf-8
from django.test import TestCase
from django.contrib.auth.models import User
from compute.models import *
from ..host import get_list, get

class HostTest(TestCase):
    def setUp(self):
        u1 = User()
        u1.username = 'apiuser'
        u1.is_active = True
        u1.api_user = True
        u1.save()
        self.u1 = u1
        
        u2 = User()
        u2.username = 'superuser'
        u2.is_active = True
        u2.is_superuser = True
        u2.api_user = True
        u2.save()
        self.u2 = u2
        
        c1 = Center()
        c1.name = '测试中心1'
        c1.location = '位置1'
        c1.desc = '备注1'
        c1.save()
        self.c1 = c1
        
        c2 = Center()
        c2.name = '测试中心2'
        c2.location = '位置2'
        c2.desc = '备注2'
        c2.save()
        self.c2 = c2
        
        g1 = Group()
        g1.center = c1
        g1.name = '测试集群1'
        g1.desc = '备注1'
        g1.save()
        g1.admin_user.add(u1)
        self.g1 = g1
        
        g2 = Group()
        g2.center = c1
        g2.name = '测试集群2'
        g2.desc = '备注2'
        g2.save()
        self.g2 = g2
        
        h1 = Host()
        h1.group = g1
        h1.ipv4 = '1.1.1.1'
        h1.enable = True
        h1.save()
        self.h1 = h1
        
        h2 = Host()
        h2.group = g2
        h2.ipv4 = '1.1.1.2'
        h2.enable = True
        h2.save()
        self.h2 = h2
        
    def test_get(self):
        res1 = get({'req_user': self.u1, 'host_id': self.h1.id})
        host = self.h1
        self.assertDictEqual(res1, {'res': True,
                                    'info': {
                                         'id': host.id,
                                         'vlan_list': [vlan.vlan for vlan in host.vlan.all()],
                                         'ipv4': host.ipv4,
                                         'vcpu_total': host.vcpu_total,
                                         'vcpu_allocated': host.vcpu_allocated,
                                         'mem_total': host.mem_total,
                                         'mem_allocated': host.mem_allocated,
                                         'mem_reserved': host.mem_reserved,
                                         'vm_limit': host.vm_limit,
                                         'vm_created': host.vm_created,
                                         'enable': host.enable
                                         }}, "")
        
        res2 = get({'req_user': self.u1, 'host_id': self.h2.id})
        self.assertDictContainsSubset({'res': False}, res2, "")
        
        res3 = get({'req_user': self.u2, 'host_id': self.h2.id})
        host = self.h2
        self.assertDictEqual(res3, {'res': True,
                                    'info': {
                                         'id': host.id,
                                         'vlan_list': [vlan.vlan for vlan in host.vlan.all()],
                                         'ipv4': host.ipv4,
                                         'vcpu_total': host.vcpu_total,
                                         'vcpu_allocated': host.vcpu_allocated,
                                         'mem_total': host.mem_total,
                                         'mem_allocated': host.mem_allocated,
                                         'mem_reserved': host.mem_reserved,
                                         'vm_limit': host.vm_limit,
                                         'vm_created': host.vm_created,
                                         'enable': host.enable
                                         }}, "")
        
    def test_get_list(self):
        res1 = get_list({'req_user': self.u1, 'group_id': self.g1.id})
        host = self.h1
        exp1 = {'res': True,
                'list': [
                    {'id':   host.id,
                    'group_id': host.group.id,
                    'ipv4': host.ipv4,
                    'vcpu_total': host.vcpu_total,
                    'vcpu_allocated': host.vcpu_allocated,
                    'mem_total': host.mem_total,
                    'mem_allocated': host.mem_allocated,
                    'mem_reserved': host.mem_reserved,
                    'vm_limit': host.vm_limit,
                    'vm_created': host.vm_created,
                    'enable': host.enable,
                    'net_types':[vlan.type.name for vlan in host.vlan.all()]}
                ]}
        self.assertDictEqual(exp1, res1, "")
        
        res2 = get_list({'req_user': self.u1, 'group_id': self.g2.id})
        exp2 = {'res': False}
        self.assertDictContainsSubset(exp2, res2, "")
        
        res3 = get_list({'req_user': self.u2, 'group_id': self.g2.id})
        host = self.h2
        exp3 = {'res': True,
                'list': [
                    {'id':   host.id,
                    'group_id': host.group.id,
                    'ipv4': host.ipv4,
                    'vcpu_total': host.vcpu_total,
                    'vcpu_allocated': host.vcpu_allocated,
                    'mem_total': host.mem_total,
                    'mem_allocated': host.mem_allocated,
                    'mem_reserved': host.mem_reserved,
                    'vm_limit': host.vm_limit,
                    'vm_created': host.vm_created,
                    'enable': host.enable,
                    'net_types':[vlan.type.name for vlan in host.vlan.all()]}
                ]}
        self.assertDictEqual(exp3, res3, "")
        
        res4 = get_list({'req_user': self.u1})
        exp4 = {'res': False}
        self.assertDictContainsSubset(exp4, res4, "")