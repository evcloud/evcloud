#coding=utf-8
from django.test import TestCase
from django.contrib.auth.models import User
from .models import DBGPU
from .api import GPUAPI
import subprocess
from api.tests.tools import create_center, create_group, create_host, create_vlantype
from api.tests.tools import create_vlan, create_ip, create_ceph_host, create_ceph_image_pool
from api.tests.tools import create_imagetype, create_xml, create_image
from api.tests.testsettings import *

from compute.api import VmAPI

def create_gpu(host, address):
    db = DBGPU()
    db.host = host
    db.address = address
    db.enable = True
    db.save()
    return db

class DeviceTest(TestCase):
    def setUp(self):
        self.vmapi = VmAPI()
        self.gpuapi = GPUAPI()

        self.c1 = create_center('测试中心1', '位置1', '备注1')
        self.c2 = create_center('测试中心2', '位置2', '备注2')
        
        self.g1 = create_group(self.c1, '测试集群1', '备注11')
        self.g2 = create_group(self.c1, '测试集群2', '备注')
        
        self.h1 = create_host(self.g1, '1.1.1.1')
        self.h2 = create_host(self.g2, '1.1.1.2')



        self.vt1 = create_vlantype('vlantype1')
        
        self.v1 = create_vlan(str(TEST_VLAN), str(TEST_BR), self.vt1)
        
        self.ip1 = create_ip(self.v1, TEST_MAC, TEST_IP)
                
        self.h1 = create_host(self.g1, str(TEST_HOST), True, [self.v1])

        self.ch1 = create_ceph_host(self.c1, str(TEST_CEPH['host']), TEST_CEPH['port'], str(TEST_CEPH['uuid']))

        self.cp1 = create_ceph_image_pool(self.ch1, TEST_CEPH['pool'])
        
        self.it1 = create_imagetype('imagetype1')
        
        self.x1 = create_xml('linux', TEST_XML)
        
        self.i1 = create_image(self.cp1, self.x1, self.it1, 'image1', 'v0.1', TEST_IMAGE)

        self.vcpu1 = 2
        self.mem1 = 2048
        self.vm1 = self.vmapi.create_vm(self.i1.id, self.vcpu1, self.mem1, host_id=self.h1.id, vlan_id=self.v1.id)
     
        self.gpu1 = create_gpu(self.h1, '0000:84:00:0')

    def tearDown(self):
        cmd = 'ssh %s virsh destroy %s' % (self.h1.ipv4, self.vm1.uuid)
        r, info = subprocess.getstatusoutput(cmd)
                    
        cmd = 'ssh %s virsh undefine %s' % (self.h1.ipv4, self.vm1.uuid)
        r, info = subprocess.getstatusoutput(cmd)
        
    
                
        cmd1 = 'ssh %s rbd rm %s/%s' % (self.cp1.host.host, self.cp1.pool, self.vm1.uuid)
        r1, info1 = subprocess.getstatusoutput(cmd1)        
                    

    def test_set_remarks(self):
        remarks = 'testseresgfsts'
        self.assertTrue(self.gpuapi.set_remarks(self.gpu1.id, remarks))
        db = DBGPU.objects.get(id = self.gpu1.id)
        self.assertEqual(db.remarks, remarks)
        
    def test_mount(self):
        mounted = self.gpuapi.mount(self.vm1.uuid, self.gpu1.id)
        self.assertTrue(mounted)
        db = DBGPU.objects.get(id = self.gpu1.id)
        self.assertEqual(db.vm, self.vm1.uuid)

        if mounted:
            self.assertTrue(self.gpuapi.umount(self.gpu1.id))
            db = DBGPU.objects.get(id=self.gpu1.id)
            self.assertEqual(db.vm, None)
