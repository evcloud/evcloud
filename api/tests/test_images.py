#coding=utf-8
from django.test import TestCase
from django.contrib.auth.models import User
from compute.models import *
from image.models import *
from storage.models import *
from ..images import get_list, get

class ImageTest(TestCase):
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
        
        c2 = Center()
        c2.name = u'测试中心2'
        c2.location = u'位置2'
        c2.desc = u'备注2'
        c2.save()
        self.c2 = c2
        
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
        
        ch1 = CephHost()
        ch1.center = c1
        ch1.host = u'0.0.0.0'
        ch1.port = 6789
        ch1.uuid = u'11111111111111'
        ch1.save()
        
        cp1 = CephPool()
        cp1.host = ch1
        cp1.pool = u'vmpool'
        cp1.type = 1
        cp1.save()
        self.cp1 = cp1
        
        ch2 = CephHost()
        ch2.center = c2
        ch2.host = u'0.0.0.0'
        ch2.port = 6789
        ch2.uuid = u'11111111111111'
        ch2.save()
        
        cp2 = CephPool()
        cp2.host = ch2
        cp2.pool = u'vmpool'
        cp2.type = 1
        cp2.save()
        self.cp2 = cp2
        
        it1 = ImageType()
        it1.code = u'code1'
        it1.name = u'imagetype1'
        it1.save()
        
        x1 = Xml()
        x1.name = u'linux'
        x1.xml = u''
        x1.save()
        
        i1 = Image()
        i1.cephpool = cp1
        i1.name = u'image1'
        i1.version = u'v0.1'
        i1.snap = u'image1@1111'
        i1.desc = u''
        i1.xml = x1
        i1.type = it1
        i1.enable = True
        i1.save()
        self.i1 = i1
        
        i2 = Image()
        i2.cephpool = cp2
        i2.name = u'image2'
        i2.version = u'v0.2'
        i2.snap = u'image1@222'
        i2.desc = u''
        i2.xml = x1
        i2.type = it1
        i2.enable = True
        i2.save()
        self.i2 = i2
        
    def test_get(self):
        res1 = get({'req_user': self.u1})
        exp1 = {'res': False}
        self.assertDictContainsSubset(exp1, res1, "")
        
        res2 = get({'req_user': self.u1, 'image_id': self.i1.id})
        image = self.i1
        exp2 = {
            'res': True,
            'info': {
                'id': image.id,
                'ceph_id': image.cephpool.id,
                'name': image.name,
                'version': image.version,
                'snap': image.snap,
                'type': image.type.name,
                'desc': image.desc 
            }}
        self.assertDictEqual(exp2, res2, "")
        
        res3 = get({'req_user': self.u1, 'image_id': self.i2.id})
        exp3 = {'res': False}
        self.assertDictContainsSubset(exp3, res3, "")
        
        res4 = get({'req_user': self.u2, 'image_id': self.i2.id})
        image = self.i2
        exp4 = {
            'res': True,
            'info': {
                'id': image.id,
                'ceph_id': image.cephpool.id,
                'name': image.name,
                'version': image.version,
                'snap': image.snap,
                'type': image.type.name,
                'desc': image.desc 
            }}
        self.assertDictEqual(exp4, res4, "")
        
    def test_get_list(self):
        res1 = get_list({'req_user': self.u1})
        exp1 = {'res': False}
        self.assertDictContainsSubset(exp1, res1, "")
        
        res2 = get_list({'req_user': self.u1, 'ceph_id': self.cp1.id})
        image = self.i1
        exp2 = {'res': True,
                'list': [
                    {
                    'id':   image.id,
                    'ceph_id': image.cephpool.id,
                    'name': image.name,
                    'version': image.version,
                    'type': image.type.name
                    }
                ]}
        self.assertDictEqual(exp2, res2, "")
        
        res3 = get_list({'req_user': self.u1, 'ceph_id': self.cp2.id})
        exp3 = {'res': False}
        self.assertDictContainsSubset(exp3, res3, "")
        
        res4 = get_list({'req_user': self.u2, 'ceph_id': self.cp2.id})
        image = self.i2
        exp4 = {'res': True,
                'list': [
                    {
                    'id':   image.id,
                    'ceph_id': image.cephpool.id,
                    'name': image.name,
                    'version': image.version,
                    'type': image.type.name
                    }
                ]}
        self.assertDictEqual(exp4, res4, "")