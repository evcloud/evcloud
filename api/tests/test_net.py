#coding=utf-8
from django.test import TestCase
from django.contrib.auth.models import User
from compute.models import *
from network.models import *
from ..net import get_vlan_list, get_vlan

class NetTest(TestCase):
    def setUp(self):
        u1 = User()
        u1.username = u'apiuser'
        u1.is_active = True
        u1.api_user = True
        u1.save()
        self.u1 = u1
        
        u2 = User()
        u2.username = u'superuser'
        u2.is_active = True
        u2.is_superuser = True
        u2.api_user = True
        u2.save()
        self.u2 = u2
        
        c1 = Center()
        c1.name = u'测试中心1'
        c1.location = u'位置1'
        c1.desc = u'备注1'
        c1.save()
        self.c1 = c1
      
        g1 = Group()
        g1.center = c1
        g1.name = u'测试集群1'
        g1.desc = u'备注1'
        g1.save()
        g1.admin_user.add(u1)
        self.g1 = g1
        
        g2 = Group()
        g2.center = c1
        g2.name = u'测试集群2'
        g2.desc = u'备注2'
        g2.save()
        self.g2 = g2
        
        vt1 = VlanType()
        vt1.code = u'vlantype1'
        vt1.name = u'vlantype1'
        vt1.save()
        
        v1 = Vlan()
        v1.vlan = u'0.0.0.0'
        v1.br = u'br1'
        v1.type = vt1
        v1.enable = True
        v1.save()
        self.v1 = v1
        
        v2 = Vlan()
        v2.vlan = u'0.0.0.1'
        v2.br = u'br2'
        v2.type = vt1
        v2.enable = False
        v2.save()
        self.v2 = v2
        
        h1 = Host()
        h1.group = g1
        h1.ipv4 = u'1.1.1.1'
        h1.enable = True
        h1.save()
        h1.vlan.add(v1)

        h2 = Host()
        h2.group = g2
        h2.ipv4 = u'1.1.1.2'
        h2.enable = True
        h2.save()
        h2.vlan.add(v2)
        
    def test_get_vlan_list(self):
        res1 = get_vlan_list({'req_user': self.u1})
        exp1 = {'res': False}
        self.assertDictContainsSubset(exp1, res1, "")
        
        res2 = get_vlan_list({'req_user': self.u1, 'group_id': self.g1.id})
        vlan = self.v1
        exp2 = {'res': True, 
                'list': [
                    {
                        'id': vlan.id,
                        'vlan': vlan.vlan,
                        'br': vlan.br,
                        'type_code': vlan.type.code,
                        'type': vlan.type.name,
                        'enable': vlan.enable
                        }]}
        self.assertDictEqual(exp2, res2, "")
        
        res3 = get_vlan_list({'req_user': self.u1, 'group_id': self.g2.id})
        exp3 = {'res': False}
        self.assertDictContainsSubset(exp3, res3, "")
        
        res4 = get_vlan_list({'req_user': self.u2, 'group_id': self.g2.id})
        vlan = self.v2
        exp4 = {'res': True, 
                'list': [
                    {
                        'id': vlan.id,
                        'vlan': vlan.vlan,
                        'br': vlan.br,
                        'type_code': vlan.type.code,
                        'type': vlan.type.name,
                        'enable': vlan.enable
                        }]}
        self.assertDictEqual(exp4, res4, "")
        
    def test_get_vlan(self):
        res1 = get_vlan({'req_user': self.u1})
        exp1 = {'res': False}
        self.assertDictContainsSubset(exp1, res1, "")
        
        res2 = get_vlan({'req_user': self.u1, 'vlan_id': self.v1.id})
        vlan = self.v1
        exp2 = {'res': True,
                'info': {
                     'id': vlan.id,
                     'vlan': vlan.vlan,
                     'br': vlan.br,
                     'type_code': vlan.type.code,
                     'type_name': vlan.type.name,
                     'enable': vlan.enable}}
        self.assertDictEqual(exp2, res2, "")
        
        res3 = get_vlan({'req_user': self.u1, 'vlan_id': self.v2.id})
        exp3 = {'res': False}
        self.assertDictContainsSubset(exp3, res3, "")
        
        res4 = get_vlan({'req_user': self.u2, 'vlan_id': self.v2.id})
        vlan = self.v2
        exp4 = {'res': True,
                'info': {
                     'id': vlan.id,
                     'vlan': vlan.vlan,
                     'br': vlan.br,
                     'type_code': vlan.type.code,
                     'type_name': vlan.type.name,
                     'enable': vlan.enable}}
        self.assertDictEqual(exp4, res4, "")