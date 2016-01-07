#coding=utf-8
from django.test import TestCase
from django.contrib.auth.models import User
from compute.models import Center, Group
from ..center import get_list

class CenterTest(TestCase):
    def setUp(self):
        u1 = User()
        u1.username = 'apitest'
        u1.is_active = True
        u1.api_user = True
        u1.save()
        self.u1 = u1
        
        c1 = Center()
        c1.name = u'测试中心'
        c1.location = u'北京'
        c1.desc = u'备注'
        c1.save()
        self.c1 = c1
        
        g1 = Group()
        g1.center = c1
        g1.name = u'测试'
        g1.desc = u'测试'
        g1.save()
        g1.admin_user.add(u1)
        self.g1 = g1
        
        c2 = Center()
        c2.name = u'测试中心2'
        c2.location = u'北京2'
        c2.desc = u'备注2'
        c2.save()
        self.c2 = c2
        
    def test_get_list(self):
        res = get_list({'req_user': self.u1})
        self.assertDictEqual(res, {'res': True, 
                                   'list': [
                                            {'id': self.c1.id, 
                                             'name': self.c1.name, 
                                             'location': self.c1.location, 
                                             'desc': self.c1.desc}
                                            ]}, 
                                    '')
        res2 = get_list({})
        self.assertDictContainsSubset({'res': False}, res2, '')