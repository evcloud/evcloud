#coding=utf-8
from django.test import TestCase
from django.contrib.auth.models import User
from compute.models import Center, Group
from ..group import get_list, get

from .tools import create_user, create_superuser, create_center, create_group

class GroupTest(TestCase):
    def setUp(self):
        self.u1 = create_user('apitest')
        self.u2 = create_superuser('superuser')
        self.c1 = create_center('测试中心1', '位置1', '备注1')
        self.c2 = create_center('测试中心2', '位置2', '备注2')
        self.g1 = create_group(self.c1, '测试集群1', '备注1', [self.u1])
        self.g2 = create_group(self.c1, 'groupname2', 'desc2')
        self.g3 = create_group(self.c2, 'groupname3', 'desc3')
        
    def test_get_err_args(self):
        #缺少参数 group_id
        req = {'req_user': self.u1}
        exp = {'res': False}
        res = get(req)
        self.assertDictContainsSubset(exp, res)

        req1 = {'req_user': self.u1, 'group_id': -1}
        res1 = get(req1)
        self.assertDictContainsSubset(exp, res1)
        
    def test_get_err_perm(self):
        #权限错误
        req = {'req_user': self.u1, 'group_id': self.g2}
        exp = {'res': False}
        res = get(req)
        self.assertDictContainsSubset(exp, res)

    def test_get(self):
        req = {'req_user': self.u1, 'group_id': self.g1.id}
        exp = {'res': True, 'info': {'id': self.g1.id,
                                     'center_id': self.g1.center_id,
                                     'name': self.g1.name,
                                     'desc': self.g1.desc,
                                     'admin_user': [user.username for user in self.g1.admin_user.all()], 
                                     'order':self.g1.order}}
        res = get(req)
        self.assertDictEqual(exp, res)
        
    def test_get_superuser(self):
        req = {'req_user': self.u2, 'group_id': self.g1.id}
        exp = {'res': True, 'info': {'id': self.g1.id,
                                     'center_id': self.g1.center_id,
                                     'name': self.g1.name,
                                     'desc': self.g1.desc,
                                     'admin_user': [user.username for user in self.g1.admin_user.all()], 
                                     'order':self.g1.order}}
        res = get(req)
        self.assertDictEqual(exp, res)

    def test_get_list_superuser_no_center_id(self):
        req = {'req_user': self.u2}
        exp = {'res': True, 'list':[
            {'id':   self.g1.id,
            'center_id': self.g1.center_id,
            'name': self.g1.name,
            'desc': self.g1.desc,
            'admin_user': [user.username for user in self.g1.admin_user.all()],
            'order': self.g1.order},
            {'id':   self.g2.id,
            'center_id': self.g2.center_id,
            'name': self.g2.name,
            'desc': self.g2.desc,
            'admin_user': [user.username for user in self.g2.admin_user.all()],
            'order': self.g2.order},
            {'id':   self.g3.id,
            'center_id': self.g3.center_id,
            'name': self.g3.name,
            'desc': self.g3.desc,
            'admin_user': [user.username for user in self.g3.admin_user.all()],
            'order': self.g3.order},
        ]}
        res = get_list(req)
        self.assertDictEqual(exp, res)

    def test_get_list_no_center_id(self):
        req = {'req_user': self.u1}
        exp = {'res': True, 'list':[
            {'id':   self.g1.id,
            'center_id': self.g1.center_id,
            'name': self.g1.name,
            'desc': self.g1.desc,
            'admin_user': [user.username for user in self.g1.admin_user.all()],
            'order': self.g1.order}
        ]}
        res = get_list(req)
        self.assertDictEqual(exp, res)

    def test_get_list_superuser(self):
        req = {'req_user': self.u2, 'center_id': self.c1.id}
        exp = {'res': True, 'list':[
            {'id':   self.g1.id,
            'center_id': self.g1.center_id,
            'name': self.g1.name,
            'desc': self.g1.desc,
            'admin_user': [user.username for user in self.g1.admin_user.all()],
            'order': self.g1.order},
            {'id':   self.g2.id,
            'center_id': self.g2.center_id,
            'name': self.g2.name,
            'desc': self.g2.desc,
            'admin_user': [user.username for user in self.g2.admin_user.all()],
            'order': self.g2.order}
        ]}
        res = get_list(req)
        self.assertDictEqual(exp, res)

    def test_get_list(self):
        req = {'req_user': self.u1, 'center_id': self.c1.id}
        exp = {'res': True, 'list':[
            {'id':   self.g1.id,
            'center_id': self.g1.center_id,
            'name': self.g1.name,
            'desc': self.g1.desc,
            'admin_user': [user.username for user in self.g1.admin_user.all()],
            'order': self.g1.order}
        ]}
        res = get_list(req)
        self.assertDictEqual(exp, res)
