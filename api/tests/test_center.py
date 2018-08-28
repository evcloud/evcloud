#coding=utf-8
from django.test import TestCase
from django.contrib.auth.models import User
from compute.models import Center, Group
from ..center import get_list

from .tools import create_user, create_group, create_center



class CenterTest(TestCase):
    def setUp(self):
        self.u1 = create_user('apitest')        
        self.c1 = create_center('测试中心', '北京', '备注')
        self.g1 = create_group(self.c1, '测试', '测试', [self.u1])
        self.c2 = create_center('测试中心2', '北京', '备注2')        
        
    def test_get_list(self):
        res = get_list({'req_user': self.u1})
        self.assertDictEqual(res, {'res': True, 
                                   'list': [
                                            {'id': self.c1.id, 
                                             'name': self.c1.name, 
                                             'location': self.c1.location, 
                                             'desc': self.c1.desc,
                                             'order': 0}
                                            ]})
        res2 = get_list({})
        self.assertDictContainsSubset({'res': False}, res2)

        res3 = get_list({'req_user': 'test'})
        self.assertDictContainsSubset({'res': False}, res3)