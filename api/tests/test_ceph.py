#coding=utf-8
from django.test import TestCase
from django.contrib.auth.models import User
from compute.models import *
from storage.models import *
from ..ceph import get_list

class CephTest(TestCase):
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
        
        ch1 = CephHost()
        ch1.center = c1
        ch1.host = '0.0.0.0'
        ch1.port = 6789
        ch1.uuid = '1111111111111111111'
        ch1.save()
        
        cp1 = CephPool()
        cp1.host = ch1
        cp1.pool = 'vmpool'
        cp1.type = 1
        cp1.save()
        self.cp1 = cp1
        
        ch2 = CephHost()
        ch2.center = c2
        ch2.host = '0.0.0.1'
        ch2.port = 6789
        ch2.uuid = '1111111111111111111'
        ch2.save()
        
        cp2 = CephPool()
        cp2.host = ch2
        cp2.pool = 'vmpool'
        cp2.type = 1
        cp2.save()
        self.cp2 = cp2
        
    def test_get_list(self):
        res1 = get_list({'req_user': self.u1, 'center_id': self.c1.id})
        self.assertDictEqual(res1, {
                                    'res': True,
                                    'list': [
                                        {
                                        'id':   self.cp1.id,
                                        'pool': self.cp1.pool,
                                        'type': self.cp1.type,
                                        'center_id': self.cp1.host.center.id,
                                        'host': self.cp1.host.host,
                                        'port': self.cp1.host.port,
                                        'uuid': self.cp1.host.uuid
                                        }]}, "")
        
        res2 = get_list({'req_user': self.u1, 'center_id': self.c2.id})
        self.assertDictContainsSubset({'res': False}, res2, "")
        res3 = get_list({'req_user': self.u2, 'center_id': self.c1.id})
        self.assertDictEqual(res3, {
                                    'res': True,
                                    'list': [
                                        {
                                        'id':   self.cp1.id,
                                        'pool': self.cp1.pool,
                                        'type': self.cp1.type,
                                        'center_id': self.cp1.host.center.id,
                                        'host': self.cp1.host.host,
                                        'port': self.cp1.host.port,
                                        'uuid': self.cp1.host.uuid
                                        }]}, "")