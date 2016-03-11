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

class VmTest(TestCase):
    vcpu = 2
    mem = 2048
    def setUp(self):
        self.u1 = create_user('apiuser1')
        self.u2 = create_user('apiuser2')
        self.u3 = create_superuser('superuser')
        self.u4 = create_user('apiuser4')

        self.c1 = create_center('1', '1', '1')

        self.g1 = create_group(self.c1, '1', '1', [self.u1, self.u4])
                
        self.vt1 = create_vlantype('vlantype1')
        
        self.v1 = create_vlan(str(TEST_VLAN), str(TEST_BR), self.vt1)
        
        self.ip1 = create_ip(self.v1, TEST_MAC, TEST_IP)
                
        self.h1 = create_host(self.g1, str(TEST_HOST), True, [self.v1])

        self.ch1 = create_ceph_host(self.c1, str(TEST_CEPH['host']), TEST_CEPH['port'], str(TEST_CEPH['uuid']))

        self.cp1 = create_ceph_image_pool(self.ch1, TEST_CEPH['pool'])
        
        self.it1 = create_imagetype('imagetype1')
        
        self.x1 = create_xml('linux', TEST_XML)
        
        self.i1 = create_image(self.cp1, self.x1, self.it1, 'image1', 'v0.1', TEST_IMAGE)

        
#     def tearDown(self):
# #         print 'tear down ========================================'
#         if self.vm_uuid:
#             if self._vm_exist(self.h1.ipv4, self.vm_uuid):
#                 cmd = 'ssh %s virsh destroy %s' % (self.h1.ipv4, self.vm_uuid)
#                 r, info = subprocess.getstatusoutput(cmd)
# #                 if r != 0:
# #                     os.system('ssh %s virsh destroy %s' % (self.h1.ipv4, self.vm_uuid))
# #                     print info
                    
#                 cmd = 'ssh %s virsh undefine %s' % (self.h1.ipv4, self.vm_uuid)
#                 r, info = subprocess.getstatusoutput(cmd)
#                 if r != 0:
#                     os.system('ssh %s virsh undefine %s' % (self.h1.ipv4, self.vm_uuid))
# #                     print info
                
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
# #                     print info1
                    
#             cmd = 'ssh %s rbd ls %s | grep %s' % (self.cp1.host.host, self.cp1.pool, self.vm_disk)
#             r, info = subprocess.getstatusoutput(cmd)
#             if r == 0:
#                 cmd1 = 'ssh %s rbd rm %s/%s' % (self.cp1.host.host, self.cp1.pool, self.vm_disk)
#                 r1, info1 = subprocess.getstatusoutput(cmd1)
#                 if r1 != 0:
#                     os.system('ssh %s rbd rm %s/%s' % (self.cp1.host.host, self.cp1.pool, self.vm_disk))
# #                     print info1
                
# #         print 'finished tear down ================================'
        
    def test_create_vm_err_args(self):
        self.assertTrue(self._host_alive(self.ip1) == False)
        req = {'req_user': self.u1, 'image_id': self.i1.id, 'vcpu': self.vcpu, 'mem': self.mem}
        exp = {'res': False}
        res = create(req)
        if res['res']:
            self.assertTrue(self._vm_exist(self.h1.ipv4, res['uuid']))
            self._del_vm(self.h1.ipv4, res['uuid'])
            self._del_ceph(self.cp1, res['uuid'])
        self.assertDictContainsSubset(exp, res)

    def test_create_vm_err_args1(self):
        self.assertTrue(self._host_alive(self.ip1) == False)
        req = {'req_user': self.u1, 'image_id': self.i1.id, 'vcpu': self.vcpu, 'mem': self.mem, 'net_type_id': self.vt1.code}
        exp = {'res': False}
        res = create(req)
        if res['res']:
            self.assertTrue(self._vm_exist(self.h1.ipv4, res['uuid']))
            self._del_vm(self.h1.ipv4, res['uuid'])
            self._del_ceph(self.cp1, res['uuid'])
        self.assertDictContainsSubset(exp, res)

    def test_create_vm_err_args2(self):
        self.assertTrue(self._host_alive(self.ip1) == False)
        req = {'req_user': self.u1, 'image_id': self.i1.id, 'vcpu': self.vcpu, 'mem': self.mem, 'group_id': self.g1.id}
        exp = {'res': False}
        res = create(req)
        if res['res']:
            self.assertTrue(self._vm_exist(self.h1.ipv4, res['uuid']))
            self._del_vm(self.h1.ipv4, res['uuid'])
            self._del_ceph(self.cp1, res['uuid'])
        self.assertDictContainsSubset(exp, res)

    def test_create_vm_nettype(self):
        self.assertTrue(self._host_alive(self.ip1) == False)
        req = {'req_user': self.u1, 'image_id': self.i1.id, 'vcpu': self.vcpu, 'mem': self.mem, 
            'net_type_id': self.vt1.code, 'group_id': self.g1.id}
        exp = {'res': True}
        res = create(req)
        if res['res']:
            self.assertTrue(self._vm_exist(self.h1.ipv4, res['uuid']))
            self._del_vm(self.h1.ipv4, res['uuid'])
            self._del_ceph(self.cp1, res['uuid'])
        self.assertDictContainsSubset(exp, res)        

    def test_create_vm_nettype1(self):
        self.assertTrue(self._host_alive(self.ip1) == False)
        req = {'req_user': self.u1, 'image_id': self.i1.id, 'vcpu': self.vcpu, 'mem': self.mem, 
            'net_type_id': self.vt1.code, 'host_id': self.h1.id}
        exp = {'res': True}
        res = create(req)
        if res['res']:
            self.assertTrue(self._vm_exist(self.h1.ipv4, res['uuid']))
            self._del_vm(self.h1.ipv4, res['uuid'])
            self._del_ceph(self.cp1, res['uuid'])
        self.assertDictContainsSubset(exp, res)        
        
    def test_create_vm_vlan(self):
        self.assertTrue(self._host_alive(self.ip1) == False)
        req = {'req_user': self.u1, 'image_id': self.i1.id, 'vcpu': self.vcpu, 'mem': self.mem, 
            'vlan_id': self.v1.id, 'group_id': self.g1.id}
        exp = {'res': True}
        res = create(req)
        if res['res']:
            self.assertTrue(self._vm_exist(self.h1.ipv4, res['uuid']))
            self._del_vm(self.h1.ipv4, res['uuid'])
            self._del_ceph(self.cp1, res['uuid'])
        self.assertDictContainsSubset(exp, res)        

    def test_create_vm_vlan1(self):
        self.assertTrue(self._host_alive(self.ip1) == False)
        req = {'req_user': self.u1, 'image_id': self.i1.id, 'vcpu': self.vcpu, 'mem': self.mem, 
            'vlan_id': self.v1.id, 'host_id': self.h1.id}
        exp = {'res': True}
        res = create(req)
        if res['res']:
            self.assertTrue(self._vm_exist(self.h1.ipv4, res['uuid']))
            self._del_vm(self.h1.ipv4, res['uuid'])
            self._del_ceph(self.cp1, res['uuid'])
        self.assertDictContainsSubset(exp, res)   

    def test_create_get_vm(self):
        self.assertTrue(self._host_alive(self.ip1) == False)
        req = {'req_user': self.u1, 'image_id': self.i1.id, 'vcpu': self.vcpu, 'mem': self.mem, 
            'net_type_id': self.vt1.code, 'group_id': self.g1.id, 'remarks': 'test11122333'}
        exp = {'res': True}
        res = create(req)
        if res['res']:
            #正常获取vm信息
            req1 = {'req_user': self.u1, 'uuid': res['uuid']}
            exp1 = {'res': True, 'info':{
                'uuid':     res['uuid'],
                'name':     res['uuid'], 
                'vcpu':     self.vcpu ,
                'mem':      self.mem ,
                'creator':       self.u1.username, 
                'remarks':       req['remarks'],
                'image_id':      self.i1.id,
                'image_snap':    self.i1.snap,
                'image':         self.i1.fullname,
                'host_id':       self.h1.id,
                'host_ipv4':     self.h1.ipv4,
                'group_id':      self.g1.id,
                'group_name':    self.g1.name,
                'center_id':     self.c1.id,
                'center_name':   self.c1.name, 
            
                'vlan_id':       self.v1.id,
                'vlan_name':     self.v1.vlan,
                'mac':           self.ip1.mac,
                'ipv4':          self.ip1.ipv4,
                
                'ceph_id':       self.cp1.id,
                'ceph_host':     self.ch1.host,
                'ceph_pool':     self.cp1.pool
            }}
            res1 = get(req1)
            self.assertTrue(res1['res'])
            if res1['res']:
                self.assertDictContainsSubset(exp1['info'], res1['info'])

            #越权获取vm信息
            req3 = {'req_user': self.u2, 'uuid': res['uuid']}
            exp3 = {'res': False}
            res3 = get(req3)
            self.assertDictContainsSubset(exp3, res3)


            self.assertTrue(self._vm_exist(self.h1.ipv4, res['uuid']))
            self._del_vm(self.h1.ipv4, res['uuid'])
            self._del_ceph(self.cp1, res['uuid'])
        self.assertDictContainsSubset(exp, res)  
     

    def test_create_get_vmlist(self):
        self.assertTrue(self._host_alive(self.ip1) == False)
        req = {'req_user': self.u1, 'image_id': self.i1.id, 'vcpu': self.vcpu, 'mem': self.mem, 
            'net_type_id': self.vt1.code, 'group_id': self.g1.id, 'remarks': 'test11122333'}
        exp = {'res': True}
        res = create(req)
        if res['res']:
            #正常获取vm列表
            req2 = {'req_user': self.u1, 'group_id': self.g1.id}
            exp2 = {'res': True, 'list':[
                {
                    'uuid':     res['uuid'],
                    'name':     res['uuid'], 
                    'group_id':      self.g1.id,
                    'group_name':    self.g1.name,
                    'center_id':     self.c1.id,
                    'center_name':   self.c1.name, 
                    'host_id':       self.h1.id,
                    'host_ipv4':     self.h1.ipv4,
                    'image_id':      self.i1.id,
                    'image':         self.i1.fullname,
                    'ipv4':          self.ip1.ipv4,
                    'vcpu':     self.vcpu ,
                    'mem':      self.mem ,
                    'remarks':       req['remarks'],
                }
            ]}
            res2 = get_list(req2)
            
            self.assertTrue(res2['res'])
            if res2['res']:
                self.assertEqual(len(res2['list']), len(exp2['list']))
                for i in range(len(exp2['list'])):
                    self.assertDictContainsSubset(exp2['list'][i], res2['list'][i])

            #越权获取vm列表
            req4 = {'req_user': self.u2, 'group_id': self.g1.id}
            exp4 = {'res': False}
            res4 = get_list(req4)
            self.assertDictContainsSubset(exp4, res4)


            self.assertTrue(self._vm_exist(self.h1.ipv4, res['uuid']))
            self._del_vm(self.h1.ipv4, res['uuid'])
            self._del_ceph(self.cp1, res['uuid'])
        self.assertDictContainsSubset(exp, res)  

    def test_create_delete_vm_db(self):
        host_pre = Host.objects.get(id = self.h1.id)
        ip_pre = MacIP.objects.get(id = self.ip1.id)

        self.assertTrue(self._host_alive(self.ip1) == False)
        req = {'req_user': self.u1, 'image_id': self.i1.id, 'vcpu': self.vcpu, 'mem': self.mem, 
            'net_type_id': self.vt1.code, 'group_id': self.g1.id}
        exp = {'res': True}
        res = create(req)
        if res['res']:
            host_aft = Host.objects.get(id = self.h1.id)
            ip_aft = MacIP.objects.get(id = self.ip1.id)
            self.assertEqual(host_pre.vcpu_allocated + self.vcpu, host_aft.vcpu_allocated)
            self.assertEqual(host_pre.mem_allocated + self.mem, host_aft.mem_allocated)
            self.assertEqual(host_pre.vm_created + 1, host_aft.vm_created)

            self.assertEqual(ip_aft.vmid, res['uuid'])

            req1 = {'req_user': self.u1, 'uuid': res['uuid'], 'op': 'delete'}
            exp1 = {'res': True}
            res1 = op(req1)
            self.assertDictContainsSubset(exp1, res1)
            if res1['res']:
                host_del = Host.objects.get(id = self.h1.id)
                ip_del = MacIP.objects.get(id = self.ip1.id)
                self.assertEqual(host_del.vcpu_allocated, host_aft.vcpu_allocated - self.vcpu)
                self.assertEqual(host_del.mem_allocated, host_aft.mem_allocated - self.mem)
                self.assertEqual(host_del.vm_created, host_aft.vm_created - 1)
                self.assertEqual(ip_del.vmid, '')

                # domain 是否删除
                self.assertFalse(self._vm_exist(self.h1.ipv4, res['uuid']))
                
                # 虚拟机记录是否删除
                vmobj = Vm.objects.filter(uuid = res['uuid'])
                self.assertFalse(vmobj.exists())
                
                # 归档记录是否添加
                vmarc = VmArchive.objects.filter(uuid = res['uuid'])
                self.assertTrue(vmarc.exists())
                self.assertTrue(vmarc.count() == 1)
                
                # 归档记录是否正确
                if vmarc.count() == 1:
                    vmarc = vmarc[0]
                    self.assertTrue(vmarc.center_id == self.c1.id)
                    self.assertTrue(vmarc.center_name == self.c1.name)
                    self.assertTrue(vmarc.group_id == self.g1.id)
                    self.assertTrue(vmarc.group_name == self.g1.name)
                    self.assertTrue(vmarc.host_id == self.h1.id)
                    self.assertTrue(vmarc.host_ipv4 == self.h1.ipv4)
                    self.assertTrue(vmarc.ceph_host == self.cp1.host.host)
                    self.assertTrue(vmarc.ceph_pool == self.cp1.pool)
                    self.assertTrue(vmarc.image_id == self.i1.id)
                    self.assertTrue(vmarc.image_snap == self.i1.snap)
                    self.assertTrue(vmarc.name == res['uuid'])
                    self.assertTrue(vmarc.uuid == res['uuid'])
                    self.assertTrue(vmarc.vcpu == self.vcpu)
                    self.assertTrue(vmarc.mem == self.mem)
                    self.assertTrue(vmarc.disk[2:-21] == res['uuid'])
                    self.assertTrue(vmarc.mac == self.ip1.mac)
                    self.assertTrue(vmarc.ipv4 == self.ip1.ipv4)
                    self.assertTrue(vmarc.vlan == self.v1.vlan)
                    self.assertTrue(vmarc.br == self.v1.br)

            self._teardownvm(res['uuid'])
        self.assertDictContainsSubset(exp, res) 

    def test_vm_op_perm(self):
        self.assertTrue(self._host_alive(self.ip1) == False)
        req = {'req_user': self.u1, 'image_id': self.i1.id, 'vcpu': self.vcpu, 'mem': self.mem, 
            'net_type_id': self.vt1.code, 'group_id': self.g1.id}
        exp = {'res': True}
        res = create(req)
        if res['res']:
            #自己
            req1 = {'req_user': self.u1, 'uuid': res['uuid'], 'op': 'reboot'}
            exp1 = {'res': True}
            res1 = op(req1)
            self.assertDictContainsSubset(exp1, res1)

            #同集群其他管理员
            req1 = {'req_user': self.u4, 'uuid': res['uuid'], 'op': 'reboot'}
            exp1 = {'res': False}
            res1 = op(req1)
            self.assertDictContainsSubset(exp1, res1)            

            #非该集群管理员
            req1 = {'req_user': self.u2, 'uuid': res['uuid'], 'op': 'reboot'}
            exp1 = {'res': False}
            res1 = op(req1)
            self.assertDictContainsSubset(exp1, res1)

            #超级管理员
            req1 = {'req_user': self.u3, 'uuid': res['uuid'], 'op': 'reboot'}
            exp1 = {'res': True}
            res1 = op(req1)
            self.assertDictContainsSubset(exp1, res1)

            self.assertTrue(self._vm_exist(self.h1.ipv4, res['uuid']))
            self._del_vm(self.h1.ipv4, res['uuid'])
            self._del_ceph(self.cp1, res['uuid'])
        self.assertDictContainsSubset(exp, res)    


    def test_edit_shutdown_start(self):
        vm_uuid = self._setupvm()
        if not vm_uuid:
            return

        #修改备注测试
        vmobj = Vm.objects.get(uuid = vm_uuid)
        hostobj = Host.objects.get(id = self.h1.id)
        remarks = 'test123'
        req = {'req_user': self.u1, 'uuid': vmobj.uuid, 'remarks': remarks}
        exp = {'res': True}
        res = edit(req)
        self.assertDictEqual(exp, res)
        self._assert_host(hostobj)
        vmobj.remarks = remarks
        self._assert_vm(vmobj)
        
        #运行状态修改
        vmobj = Vm.objects.get(uuid = vm_uuid)
        hostobj = Host.objects.get(id = self.h1.id)
        vcpu = 3
        mem = 3000
        req1 = {'req_user': self.u1, 'uuid': vmobj.uuid, 'vcpu': vcpu, 'mem': mem}
        exp1 = {'res': False}
        res1 = edit(req1)
        self.assertDictContainsSubset(exp1, res1)
        self._assert_host(hostobj)
        self._assert_vm(vmobj)

        #poweroff操作测试
        req11 = {'req_user': self.u1, 'uuid': vmobj.uuid, 'op':'poweroff'}
        exp11 = {'res': True}
        res11 = op(req11)
        self.assertDictEqual(exp11, res11)

        if res11['res']:
            #状态
            req6 = {'req_user': self.u1, 'uuid': vm_uuid}
            conn = libvirt.open("qemu+ssh://%s/system" % self.h1.ipv4)
            domain = conn.lookupByUUIDString(vm_uuid)
            info = domain.info()
            exp6 = {'res': True, 'status': info[0]}
            res6 = status(req6)
            self.assertDictEqual(exp6, res6)

            #修改cpu测试
            vmobj = Vm.objects.get(uuid = vm_uuid)
            hostobj = Host.objects.get(id = self.h1.id)
            vcpu = 4
            req2 = {'req_user': self.u1, 'uuid': vmobj.uuid, 'vcpu': vcpu}
            exp2 = {'res': True}
            res2 = edit(req2)
            self.assertDictEqual(exp2, res2)

            hostobj.vcpu_allocated = hostobj.vcpu_allocated - vmobj.vcpu + vcpu
            self._assert_host(hostobj)
            
            vmobj.vcpu = vcpu
            self._assert_vm(vmobj)
            
            #修改mem测试
            vmobj = Vm.objects.get(uuid = vm_uuid)
            hostobj = Host.objects.get(id = self.h1.id)
            mem = 4096
            req3 = {'req_user': self.u1, 'uuid': vmobj.uuid, 'mem': mem}
            exp3 = {'res': True}
            res3 = edit(req3)
            self.assertDictEqual(exp3, res3)
            
            hostobj.mem_allocated = hostobj.mem_allocated - vmobj.mem + mem
            self._assert_host(hostobj)

            vmobj.mem = mem
            self._assert_vm(vmobj)

            #修改cpu和mem测试
            vmobj = Vm.objects.get(uuid = vm_uuid)
            hostobj = Host.objects.get(id = self.h1.id)
            vcpu = 3
            mem = 3000
            req4 = {'req_user': self.u1, 'uuid': vmobj.uuid, 'vcpu': vcpu, 'mem': mem}
            exp4 = {'res': True}
            res4 = edit(req4)
            self.assertDictEqual(exp4, res4)
            
            hostobj.vcpu_allocated = hostobj.vcpu_allocated - vmobj.vcpu + vcpu
            hostobj.mem_allocated = hostobj.mem_allocated - vmobj.mem + mem
            self._assert_host(hostobj)

            vmobj.vcpu = vcpu
            vmobj.mem = mem
            self._assert_vm(vmobj)

            #start操作测试
            req5 = {'req_user': self.u1, 'uuid': vmobj.uuid, 'op': 'start'}
            exp5 = {'res': True}
            res5 = op(req5)
            self.assertDictEqual(exp5, res5)

            

        self._teardownvm(vm_uuid)

       
    def test_op_reset(self):
        vm_uuid = self._setupvm()
        if not vm_uuid:
            return
        
        def get_disk_count(host, pool, disk):
            cmd = 'ssh %s rbd ls %s | grep ^%s | wc -l' % (host, pool, disk)
            r, info = subprocess.getstatusoutput(cmd)
            if r == 0:
                return int(info)
            return -1
        
        #非关机状态判断
        disk_count = get_disk_count(self.cp1.host.host, self.cp1.pool, vm_uuid)
        x_disk_count = get_disk_count(self.cp1.host.host, self.cp1.pool, 'x_'+vm_uuid)
        res1 = op({'req_user': self.u1, 'uuid': vm_uuid, 'op': 'reset'})
        exp1 = {'res': False}
        self.assertDictContainsSubset(exp1, res1)
        self.assertEqual(disk_count, get_disk_count(self.cp1.host.host, self.cp1.pool, vm_uuid))
        self.assertEqual(x_disk_count, get_disk_count(self.cp1.host.host, self.cp1.pool, 'x_'+vm_uuid))
        
        conn = libvirt.open("qemu+ssh://%s/system" % self.h1.ipv4)
        domain = conn.lookupByUUIDString(vm_uuid)
        domain.destroy()
        
        #常规测试
        disk_count = get_disk_count(self.cp1.host.host, self.cp1.pool, vm_uuid)
        x_disk_count = get_disk_count(self.cp1.host.host, self.cp1.pool, 'x_'+vm_uuid)
        res2 = op({'req_user': self.u1, 'uuid': vm_uuid, 'op': 'reset'})
        exp2 = {'res': True}
        self.assertDictEqual(exp2, res2)
        self.assertEqual(disk_count, get_disk_count(self.cp1.host.host, self.cp1.pool, vm_uuid))
        self.assertEqual(x_disk_count + 1, get_disk_count(self.cp1.host.host, self.cp1.pool, 'x_'+vm_uuid))
        
        

    def _setupvm(self):
        req = {'req_user': self.u1, 'image_id': self.i1.id, 'vcpu': self.vcpu, 'mem': self.mem, 
            'net_type_id': self.vt1.code, 'group_id': self.g1.id}
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
