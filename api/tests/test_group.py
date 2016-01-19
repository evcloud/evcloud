#coding=utf-8
from django.test import TestCase
from django.contrib.auth.models import User
from compute.models import Center, Group
from ..group import get_list, get

class GroupTest(TestCase):
    def setUp(self):
        u1 = User()
        u1.username = 'apitest'
        u1.is_active = True
        u1.api_user = True
        u1.save()
        
        u2 = User()
        u2.username = 'superuser'
        u2.is_active = True
        u2.is_superuser = True
        u2.api_user = True
        u2.save()
        
        c1 = Center()
        c1.name = '测试中心1'
        c1.location = '位置1'
        c1.desc = '备注1'
        c1.save()
        
        g1 = Group()
        g1.center = c1
        g1.name = '测试集群1'
        g1.desc = '备注1'
        g1.save()
        g1.admin_user.add(u1)
        
        g2 = Group()
        g2.center = c1
        g2.name = 'groupname2'
        g2.desc = 'desc2'
        g2.save()
        
        c2 = Center()
        c2.name = '测试中心2'
        c2.location = '位置2'
        c2.desc = '备注2'
        c2.save()
        
        g3 = Group()
        g3.center = c2
        g3.name = 'groupname3'
        g3.desc = 'desc3'
        g3.save()
        
        self.u1 = u1
        self.u2 = u2
        self.c1 = c1
        self.c2 = c2
        self.g1 = g1
        self.g2 = g2
        self.g3 = g3
        
    def test_get(self):
        res1 = get({'req_user': self.u1})
        exp1 = {'res': False}
        self.assertDictContainsSubset(exp1, res1)
        
        res2 = get({'req_user': self.u1, 'group_id': self.g1.id})
        exp2 = {'res': True, 'info': {'id': self.g1.id,
                                     'center_id': self.g1.center_id,
                                     'name': self.g1.name,
                                     'desc': self.g1.desc,
                                     'admin_user': [user.username for user in self.g1.admin_user.all()]}}
        self.assertDictEqual(exp2, res2)
        
        res3 = get({'req_user': self.u2, 'group_id': self.g1.id})
        self.assertDictContainsSubset(exp2, res3)
        
        res4 = get({'req_user': self.u1, 'group_id': self.g2.id})
        self.assertDictContainsSubset(exp1, res4)
        
    def test_get_list(self):

#         res1 = get_list({'req_user': self.u1})
#         self.assertDictContainsSubset({'res': False}, res1, '')
        
        res2 = get_list({'req_user': self.u1, 'center_id': self.c1.id})
        self.assertDictEqual(res2, {
                                    'res': True,
                                    'list': [
                                        {'id': self.g1.id,
                                         'center_id': self.g1.center_id,
                                         'name': self.g1.name,
                                         'desc': self.g1.desc,
                                         'admin_user': [user.username for user in self.g1.admin_user.all()]}
                                             ]
                                    }, '')
        
        res3 = get_list({'req_user': self.u2, 'center_id': self.c1.id})
        self.assertDictEqual(res3, {
                                    'res': True,
                                    'list': [
                                        {'id': self.g1.id,
                                         'center_id': self.g1.center_id,
                                         'name': self.g1.name,
                                         'desc': self.g1.desc,
                                         'admin_user': [user.username for user in self.g1.admin_user.all()]},
                                        {'id': self.g2.id,
                                         'center_id': self.g2.center_id,
                                         'name': self.g2.name,
                                         'desc': self.g2.desc,
                                         'admin_user': [user.username for user in self.g2.admin_user.all()]}
                                             ]}, "")