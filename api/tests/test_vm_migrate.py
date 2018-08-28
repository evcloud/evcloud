#coding=utf-8
from django.test import TestCase
from django.contrib.auth.models import User
from compute.models import *
from network.models import *
from storage.models import *
from image.models import *
from ..vm import get, get_list, create, status, op, edit, migrate
from .testsettings import *

import subprocess, os, libvirt, time

from .tools import create_user, create_superuser
from .tools import create_center, create_group, create_host
from .tools import create_vlantype, create_vlan, create_ip
from .tools import create_ceph_host, create_ceph_image_pool
from .tools import create_imagetype, create_image, create_xml

class VmMigrateTest(TestCase):
    vcpu = 2
    mem = 2048
    def setUp(self):
        self.u1 = create_user('apiuser')
        self.u2 = create_user('apiuser1')
        self.u3 = create_superuser('superuser')

        self.c1 = create_center('1','1','1')
        self.g1 = create_group(self.c1, '1', '1', [self.u1])
                
        self.vt1 = create_vlantype('vlantype1')
        
        self.v1 =  create_vlan(str(TEST_VLAN), str(TEST_BR), self.vt1)

        self.ip1 = create_ip(self.v1, TEST_MAC, TEST_IP)
                
        self.h1 = create_host(self.g1, str(TEST_HOST), True, [self.v1])
        self.h2 = create_host(self.g1, str(TEST_HOST_2), True, [self.v1])

        self.ch1 = create_ceph_host(self.c1, str(TEST_CEPH['host']), TEST_CEPH['port'], str(TEST_CEPH['uuid']))

        self.cp1 = create_ceph_image_pool(self.ch1, TEST_CEPH['pool'])
        
        self.it1 = create_imagetype('imagetype1')
        
        self.x1 = create_xml('linux', TEST_XML)
        
        self.i1 = create_image(self.cp1, self.x1, self.it1, 'image1', 'v0.1', TEST_IMAGE)
        
        self.vm_uuid = None
        self.vm_disk = None
        
#     def tearDown(self):
# #         print 'tear down ========================================'
#         if self.vm_uuid:
#             vmobj = Vm.objects.get(uuid = self.vm_uuid)
#             if self._vm_exist(vmobj.host.ipv4, self.vm_uuid):
#                 cmd = 'ssh %s virsh destroy %s' % (vmobj.host.ipv4, self.vm_uuid)
#                 r, info = subprocess.getstatusoutput(cmd)
# #                 if r != 0:
# #                     os.system('ssh %s virsh destroy %s' % (self.h1.ipv4, self.vm_uuid))
# #                     print info
                    
#                 cmd = 'ssh %s virsh undefine %s' % (vmobj.host.ipv4, self.vm_uuid)
#                 r, info = subprocess.getstatusoutput(cmd)
#                 if r != 0:
#                     os.system('ssh %s virsh undefine %s' % (vmobj.host.ipv4, self.vm_uuid))
#                     print(info)
                
#             if not self.vm_disk:
#                 self.vm_disk  = 'test_'+self.vm_uuid
                
#         if self.vm_disk:
#             cmd = 'ssh %s rbd ls %s | grep x_%s' % (self.cp1.host.host, self.cp1.pool, self.vm_disk)
#             r, info = subprocess.getstatusoutput(cmd)
#             if r == 0:
#                 cmd1 = 'ssh %s rbd rm %s/x_%s' % (self.cp1.host.host, self.cp1.pool, self.vm_disk)
#                 r1, info1 = subprocess.getstatusoutput(cmd1)
#                 if r1 != 0:
#                     os.system('ssh %s rbd rm %s/x_%s' % (self.cp1.host.host, self.cp1.pool, self.vm_disk))
#                     print(info1)
                    
#             cmd = 'ssh %s rbd ls %s | grep %s' % (self.cp1.host.host, self.cp1.pool, self.vm_disk)
#             r, info = subprocess.getstatusoutput(cmd)
#             if r == 0:
#                 cmd1 = 'ssh %s rbd rm %s/%s' % (self.cp1.host.host, self.cp1.pool, self.vm_disk)
#                 r1, info1 = subprocess.getstatusoutput(cmd1)
#                 if r1 != 0:
#                     os.system('ssh %s rbd rm %s/%s' % (self.cp1.host.host, self.cp1.pool, self.vm_disk))
#                     print(info1)
                
# #         print 'finished tear down ================================'
    


    def test_migrate_args(self):
        vm_uuid = self._setupvm()
        if not vm_uuid:
            return
        
        conn = libvirt.open("qemu+ssh://%s/system" % self.h1.ipv4)
        domain = conn.lookupByUUIDString(vm_uuid)
        domain.destroy()
        
        res1 = migrate({})
        exp1 = {'res': False}
        self.assertDictContainsSubset(exp1, res1)
        
        res2 = migrate({'req_user': self.u1})
        self.assertDictContainsSubset(exp1, res2)
        
        res3 = migrate({'req_user': self.u1, 'uuid': vm_uuid})
        self.assertDictContainsSubset(exp1, res3)
        
        res4 = migrate({'req_user': self.u1, 'host_id': self.h2.id})
        self.assertDictContainsSubset(exp1, res4)
    
        self._teardownvm(vm_uuid)
    
    def test_migrate_when_running(self):
        vm_uuid = self._setupvm()
        if not vm_uuid:
            return
        res1 = migrate({'req_user': self.u1, 'uuid': vm_uuid, 'host_id': self.h2.id})
        exp1 = {'res': False}
        self.assertDictContainsSubset(exp1, res1)

        self._teardownvm(vm_uuid)

    def test_migrate_same_host(self):
        vm_uuid = self._setupvm()
        if not vm_uuid:
            return
        
        conn = libvirt.open("qemu+ssh://%s/system" % self.h1.ipv4)
        domain = conn.lookupByUUIDString(vm_uuid)
        domain.destroy()
        
        res1 = migrate({'req_user': self.u1, 'uuid': vm_uuid, 'host_id': self.h1.id})
        exp1 = {'res': False}
        self.assertDictContainsSubset(exp1, res1)

        self._teardownvm(vm_uuid)

    def test_migrate(self):
        vm_uuid = self._setupvm()
        if not vm_uuid:
            return 
        
        conn = libvirt.open("qemu+ssh://%s/system" % self.h1.ipv4)
        domain = conn.lookupByUUIDString(vm_uuid)
        domain.destroy()
        
        host1_pre = Host.objects.get(id=self.h1.id)
        host2_pre = Host.objects.get(id=self.h2.id)

        res1 = migrate({'req_user': self.u1, 'uuid': vm_uuid, 'host_id': self.h2.id})
        exp1 = {'res': True}
        self.assertDictEqual(exp1, res1)
        
        vmobj = Vm.objects.get(uuid = vm_uuid)
        self.assertTrue(vmobj.host.id == self.h2.id)
        
        host1_pre.vcpu_allocated -= vmobj.vcpu
        host1_pre.mem_allocated -= vmobj.mem
        host1_pre.vm_created -= 1
        host2_pre.vcpu_allocated += vmobj.vcpu
        host2_pre.mem_allocated += vmobj.mem
        host2_pre.vm_created += 1
        self._assert_host(host1_pre)
        self._assert_host(host2_pre)

        self._teardownvm(vm_uuid)
        
    def _setupvm(self):
        req = {'req_user': self.u1, 'image_id': self.i1.id, 'vcpu': self.vcpu, 'mem': self.mem, 
            'net_type_id': self.vt1.code, 'host_id': self.h1.id}
        res = create(req)
        if res['res']:
            return res['uuid']
        return False

    def _teardownvm(self, vm_uuid):
        self._del_vm(self.h1.ipv4, vm_uuid)
        self._del_ceph(self.cp1, vm_uuid)

    def _host_alive(self, ipv4):
        cmd = 'fping %s -c %d' % (ipv4, 1)
#         print cmd
        res, info = subprocess.getstatusoutput(cmd)
#         print info
        if res == 0:
            return True
        return False
    
    def _disk_exist(self, cephpool, disk_uuid):
        cmd = 'ssh %s rbd ls %s | grep %s' % (cephpool.host.host, cephpool.pool, disk_uuid)
        r, info = subprocess.getstatusoutput(cmd)
        if r == 0:
            return True
        return False

    def _vm_exist(self, host_ip, vm_uuid):
        cmd = 'ssh %s virsh list --all | grep %s' % (host_ip, vm_uuid) 
        r, info = subprocess.getstatusoutput(cmd)
        if r == 0:
            return True
        return False

    def _del_ceph(self, cephpool, disk_uuid):
        if self._disk_exist(cephpool, disk_uuid):
            try:
                cmd = 'ssh %s rbd rm %s/%s' % (cephpool.host.host, cephpool.pool, disk_uuid)
                r, info = subprocess.getstatusoutput(cmd)
                if r != 0:
                    os.system('ssh %s rbd rm %s/%s' % (cephpool.host.host, cephpool.pool, disk_uuid))
            except:pass

    def _del_vm(self, host_ip, vm_uuid):
        if self._vm_exist(host_ip, vm_uuid):
            try:
                cmd = 'ssh %s virsh destroy %s' % (host_ip, vm_uuid)
                r, info = subprocess.getstatusoutput(cmd)
                if r != 0:
                    os.system('ssh %s virsh destroy %s' % (host_ip, vm_uuid))
                    # print info
                    
                cmd = 'ssh %s virsh undefine %s' % (host_ip, vm_uuid)
                r, info = subprocess.getstatusoutput(cmd)
                if r != 0:
                    os.system('ssh %s virsh undefine %s' % (host_ip, vm_uuid))
                    # print info
            except:pass
    
    def _assert_vm(self, vm_tmp):
        vmobj = Vm.objects.get(id = vm_tmp.id)
        self.assertTrue(vmobj.vcpu == vm_tmp.vcpu)
        self.assertTrue(vmobj.mem == vm_tmp.mem)
        
    def _assert_host(self, host_tmp):
        hostobj = Host.objects.get(pk = host_tmp.pk)
        self.assertTrue(hostobj.vcpu_total == host_tmp.vcpu_total)
        self.assertTrue(hostobj.vcpu_allocated == host_tmp.vcpu_allocated)
        self.assertTrue(hostobj.mem_total == host_tmp.mem_total)
        self.assertTrue(hostobj.mem_allocated == host_tmp.mem_allocated)
        self.assertTrue(hostobj.mem_reserved == host_tmp.mem_reserved)
        self.assertTrue(hostobj.vm_limit == host_tmp.vm_limit)
        self.assertTrue(hostobj.vm_created == host_tmp.vm_created)
                      
        