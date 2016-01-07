#coding=utf-8
from django.test import TestCase
from django.contrib.auth.models import User
from compute.models import *
from network.models import *
from storage.models import *
from image.models import *
from ..vm import get, get_list, create, status, op, edit, migrate
from testsettings import *

import commands, os, libvirt, time
from __builtin__ import True


class VmTest(TestCase):
    vcpu = 2
    mem = 2048
    def setUp(self):
        u1 = User()
        u1.username = u'apiuser'
        u1.is_active = True
        u1.api_user = True
        u1.save()
        self.u1 = u1
        
        u2 = User()
        u2.username = u'apiuser1'
        u2.is_active = True
        u2.api_user = True
        u2.save()
        self.u2 = u2

        u3 = User()
        u3.username = u'superuser'
        u3.is_active = True
        u3.api_user = True
        u3.is_superuser = True
        u3.save()
        self.u3 = u3

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
                
        vt1 = VlanType()
        vt1.code = u'vlantype1'
        vt1.name = u'vlantype1'
        vt1.save()
        self.vt1 = vt1
        
        v1 = Vlan()
        v1.vlan = unicode(TEST_VLAN)
        v1.br = unicode(TEST_BR)
        v1.type = vt1
        v1.enable = True
        v1.save()
        self.v1 = v1
        
        ip1 = MacIP()
        ip1.vlan = v1
        ip1.mac = TEST_MAC
        ip1.ipv4 = TEST_IP
        ip1.save()
        self.ip1 = ip1
                
        h1 = Host()
        h1.group = g1
        h1.ipv4 = unicode(TEST_HOST)
        h1.enable = True
        h1.save()
        h1.vlan.add(v1)
        self.h1 = h1
        
        ch1 = CephHost()
        ch1.center = c1
        ch1.host = unicode(TEST_CEPH['host'])
        ch1.port = TEST_CEPH['port']
        ch1.uuid = unicode(TEST_CEPH['uuid'])
        ch1.save()
        
        cp1 = CephPool()
        cp1.host = ch1
        cp1.pool = TEST_CEPH['pool']
        cp1.type = 1
        cp1.save()
        self.cp1 = cp1
        
        it1 = ImageType()
        it1.code = u'code1'
        it1.name = u'imagetype1'
        it1.save()
        
        x1 = Xml()
        x1.name = u'linux'
        x1.xml = TEST_XML
        x1.save()
        
        i1 = Image()
        i1.cephpool = cp1
        i1.name = u'image1'
        i1.version = u'v0.1'
        i1.snap = TEST_IMAGE
        i1.desc = u''
        i1.xml = x1
        i1.type = it1
        i1.enable = True
        i1.save()
        self.i1 = i1
        
        self.vm_uuid = None
        self.vm_disk = None
        
    def tearDown(self):
#         print 'tear down ========================================'
        if self.vm_uuid:
            if self._vm_exist(self.h1.ipv4, self.vm_uuid):
                cmd = 'ssh %s virsh destroy %s' % (self.h1.ipv4, self.vm_uuid)
                r, info = commands.getstatusoutput(cmd)
#                 if r != 0:
#                     os.system('ssh %s virsh destroy %s' % (self.h1.ipv4, self.vm_uuid))
#                     print info
                    
                cmd = 'ssh %s virsh undefine %s' % (self.h1.ipv4, self.vm_uuid)
                r, info = commands.getstatusoutput(cmd)
                if r != 0:
                    os.system('ssh %s virsh undefine %s' % (self.h1.ipv4, self.vm_uuid))
#                     print info
                
            if not self.vm_disk:
                self.vm_disk  = 'test_'+self.vm_uuid
                
        if self.vm_disk:
            cmd = 'ssh %s rbd ls %s | grep x_%s' % (self.cp1.host.host, self.cp1.pool, self.vm_disk)
            r, info = commands.getstatusoutput(cmd)
            if r == 0:
                cmd1 = 'ssh %s rbd rm %s/x_%s' % (self.cp1.host.host, self.cp1.pool, self.vm_disk)
                r1, info1 = commands.getstatusoutput(cmd1)
                if r1 != 0:
                    os.system('ssh %s rbd rm %s/x_%s' % (self.cp1.host.host, self.cp1.pool, self.vm_disk))
#                     print info1
                    
            cmd = 'ssh %s rbd ls %s | grep %s' % (self.cp1.host.host, self.cp1.pool, self.vm_disk)
            r, info = commands.getstatusoutput(cmd)
            if r == 0:
                cmd1 = 'ssh %s rbd rm %s/%s' % (self.cp1.host.host, self.cp1.pool, self.vm_disk)
                r1, info1 = commands.getstatusoutput(cmd1)
                if r1 != 0:
                    os.system('ssh %s rbd rm %s/%s' % (self.cp1.host.host, self.cp1.pool, self.vm_disk))
#                     print info1
                
#         print 'finished tear down ================================'
        
        
    def _host_alive(self, ipv4):
        cmd = 'ping %s -c %d' % (ipv4, 3)
#         print cmd
        res, info = commands.getstatusoutput(cmd)
#         print info
        if res == 0:
            return True
        return False
    
    def _vm_exist(self, host_ip, vm_uuid):
        cmd = 'ssh %s virsh list --all | grep %s' % (host_ip, vm_uuid) 
        r, info = commands.getstatusoutput(cmd)
        if r == 0:
            return True
        return False

    def test_create(self):
        self.assert_(self._host_alive(self.ip1) == False)
        
        res1 = create({'req_user': self.u1})
        exp1 = {'res': False}
        self.assertDictContainsSubset(exp1, res1)
        
        res2 = create({'req_user': self.u1, 
                       'group_id': self.g1.id, 
                       'image_id': self.i1.id, 
                       'net_type_id': self.vt1.pk, 
                       'vcpu': self.vcpu, 
                       'mem': self.mem})
        exp2 = {'res': True}
        self.assertDictContainsSubset(exp2, res2)  #创建是否成功
        self.vm_uuid = res2['uuid']
        
        r = self._vm_exist(self.h1.ipv4, self.vm_uuid)
        self.assert_(r, '')# 查看虚拟机是否存在
        vmobj = Vm.objects.filter(uuid = self.vm_uuid)
        self.assert_(vmobj.exists(), '') #数据库vm记录是否存在
        vmobj= vmobj[0]
        
        #数据库 vm 是否正常
        self.assert_(vmobj.host == self.h1)
        self.assert_(vmobj.image_id == self.i1.pk)
        self.assert_(vmobj.image_snap == self.i1.snap)
        self.assert_(vmobj.vcpu == self.vcpu)
        self.assert_(vmobj.mem == self.mem)
          
        self.newvm = vmobj
          
        self.vm_disk = vmobj.disk
        #数据库 宿主机修改是否正常
        host = Host.objects.get(pk = self.h1.pk)
        self.assert_(host.vcpu_total == self.h1.vcpu_total)
        self.assert_(host.vcpu_allocated == self.vcpu)
        self.assert_(host.mem_total == self.h1.mem_total)
        self.assert_(host.mem_allocated == self.mem)
        self.assert_(host.mem_reserved == self.h1.mem_reserved)
        self.assert_(host.vm_limit == self.h1.vm_limit)
        self.assert_(host.vm_created == 1) 
        
        macip = MacIP.objects.get(pk = self.ip1.pk)
        self.assert_(macip.vmid == self.vm_uuid ) #数据库ip记录修改是否正常

    def _setupvm(self):
        res = create({'req_user': self.u1, 
                      'group_id': self.g1.id, 
                      'image_id': self.i1.id, 
                      'net_type_id': self.vt1.pk, 
                      'vcpu': self.vcpu, 
                      'mem': self.mem})
        if not res['res']:
            return False
        
        self.newvm = Vm.objects.get(uuid = res['uuid'])
        self.vm_uuid = self.newvm.uuid
        self.vm_disk = self.newvm.disk
        return True
    
    def test_get(self):
        res1 = get({'req_user': self.u1})
        exp1 = {'res': False}
        self.assertDictContainsSubset(exp1, res1)
        
        if not self._setupvm():
            return
         
        res2 = get({'req_user': self.u1, 'uuid': self.newvm.uuid})
        exp2 = {'res': True,
                'info': {
                    'uuid':  self.newvm.uuid,
                    'name':   self.newvm.name, 
                    'vcpu':   self.newvm.vcpu ,
                    'mem':    self.newvm.mem ,
                    'creator':       self.newvm.creator, 
                    'create_time':   self.newvm.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'remarks':       self.newvm.remarks,
                    'deleted':       self.newvm.deleted,
                    'image_id':      self.newvm.image_id,
                    'image_snap':    self.newvm.image_snap,
                    'image':         self.newvm.image,
                    'host_id':       self.newvm.host_id,
                    'host_ipv4':     self.newvm.host.ipv4,
                    'group_id':      self.newvm.host.group_id,
                    'group_name':    self.newvm.host.group.name,
                    'center_id':     self.newvm.host.group.center_id,
                    'center_name':   self.newvm.host.group.center.name, 
                
                    'vlan_id':       self.v1.id,
                    'vlan_name':     self.v1.vlan,
                    'mac':           self.ip1.mac,
                    'ipv4':          self.ip1.ipv4,
                    
                    'ceph_id':       self.cp1.id,
                    'ceph_host':     self.cp1.host.host,
                    'ceph_pool':     self.cp1.pool 
                }
            }
        self.assertDictEqual(exp2, res2)
        
        res3 = get({'req_user': self.u2, 'uuid': self.newvm.uuid})
        exp3 = {'res': False}
        self.assertDictContainsSubset(exp3, res3)
        
        res4 = get({'req_user': self.u3, 'uuid': self.newvm.uuid})
        self.assertDictEqual(exp2, res4)
        
    def test_get_list(self):
        res1 = get_list({'req_user': self.u1})
        exp1 = {'res': False}
        self.assertDictContainsSubset(exp1, res1)
        
        if not self._setupvm():
            return
        
        res2 = get_list({'req_user': self.u1, 'group_id': self.g1.id})
        vm = self.newvm
        exp2 = {'res': True,
                'list': [
                    {
                        'uuid':         vm.uuid,
                        'name':         vm.name,
                        'center_id':    vm.host.group.center.id,
                        'center_name':  vm.host.group.center.name,
                        'group_id':     vm.host.group.id,
                        'group_name':   vm.host.group.name,
                        'host_id':      vm.host.id,
                        'host_ipv4':    vm.host.ipv4,
                        'image_id':     vm.image_id,
                        'image':        vm.image,
                        'ipv4':         self.ip1.ipv4,
                        'vcpu':         vm.vcpu,
                        'mem':          vm.mem,
                        'creator':      vm.creator,
                        'create_time':  vm.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'remarks':      vm.remarks
                    } 
                ]
            }
        self.assertDictEqual(exp2, res2)
        
        res3 = get_list({'req_user': self.u2, 'group_id': self.g1.id})
        vm = self.newvm
        exp3 = {'res': False}
        self.assertDictContainsSubset(exp3, res3)
        
        res4 = get_list({'req_user': self.u3, 'group_id': self.g1.id})
        self.assertDictEqual(exp2, res4)
        
    def test_status(self):
        res1 = status({'req_user': self.u1})
        exp1 = {'res': False}
        self.assertDictContainsSubset(exp1, res1)
        
        if not self._setupvm():
            return
        
        conn = libvirt.open("qemu+ssh://%s/system" % self.h1.ipv4)
        domain = conn.lookupByUUIDString(self.newvm.uuid)
        info = domain.info()
        
        res2 = status({'req_user': self.u1, 'uuid': self.newvm.uuid})
        exp2 = {'res': True, 'status': info[0]}
        self.assertDictEqual(exp2, res2)
        
        res3 = status({'req_user': self.u2, 'uuid': self.newvm.uuid})
        exp3 = {'res': False}
        self.assertDictContainsSubset(exp3, res3)
        
        res4 = status({'req_user': self.u3, 'uuid': self.newvm.uuid})
        self.assertDictEqual(exp2, res4)
        
    def test_op_reboot(self):
        res1 = op({'req_user': self.u1})
        exp1 = {'res': False}
        self.assertDictContainsSubset(exp1, res1)
        
        if not self._setupvm():
            return
        
        res2 = op({'req_user': self.u1, 'uuid': self.newvm.uuid, 'op': 'test'})
        exp2 = {'res': False}
        self.assertDictContainsSubset(exp2, res2)
        
        res3 = op({'req_user': self.u1, 'uuid': self.newvm.uuid, 'op': 'reboot'})
        exp3 = {'res': True}
        self.assertDictEqual(exp3, res3)
        
        res4 = op({'req_user': self.u2, 'uuid': self.newvm.uuid, 'op': 'reboot'})
        exp4 = {'res': False}
        self.assertDictContainsSubset(exp4, res4)
        
        res5 = op({'req_user': self.u3, 'uuid': self.newvm.uuid, 'op': 'reboot'})
        exp5 = {'res': True}
        self.assertDictEqual(exp5, res5)
        
    def test_op_start(self):
        if not self._setupvm():
            return
        conn = libvirt.open("qemu+ssh://%s/system" % self.h1.ipv4)
        domain = conn.lookupByUUIDString(self.newvm.uuid)
        domain.destroy()
        
        res1 = op({'req_user': self.u1, 'uuid': self.newvm.uuid, 'op': 'start'})
        exp1 = {'res': True}
        self.assertDictEqual(exp1, res1)
        self.assert_(domain.info()[0] == 1)
        
    def test_op_poweroff(self):
        if not self._setupvm():
            return
        conn = libvirt.open("qemu+ssh://%s/system" % self.h1.ipv4)
        domain = conn.lookupByUUIDString(self.newvm.uuid)
        
        res1 = op({'req_user': self.u1, 'uuid': self.newvm.uuid, 'op': 'poweroff'})
        exp1 = {'res': True}
        self.assertDictEqual(exp1, res1)
        self.assert_(domain.info()[0] == 5)
        
    def test_op_shutdown(self):
        if not self._setupvm():
            return
        conn = libvirt.open("qemu+ssh://%s/system" % self.h1.ipv4)
        domain = conn.lookupByUUIDString(self.newvm.uuid)
        time.sleep(30)
        res1 = op({'req_user': self.u1, 'uuid': self.newvm.uuid, 'op': 'shutdown'})
        time.sleep(30)
        exp1 = {'res': True}
        self.assertDictEqual(exp1, res1)
        self.assert_(domain.info()[0] == 5)
        
    def test_op_reset(self):
        if not self._setupvm():
            return
        
        def get_disk_count(host, pool, disk):
            cmd = 'ssh %s rbd ls %s | grep ^%s | wc -l' % (host, pool, disk)
            r, info = commands.getstatusoutput(cmd)
            if r == 0:
                return int(info)
            return -1
        
        
        #非关机状态判断
        disk_count = get_disk_count(self.cp1.host.host, self.cp1.pool, self.newvm.disk)
        x_disk_count = get_disk_count(self.cp1.host.host, self.cp1.pool, 'x_'+self.newvm.disk)
        res1 = op({'req_user': self.u1, 'uuid': self.newvm.uuid, 'op': 'reset'})
        exp1 = {'res': False}
        self.assertDictContainsSubset(exp1, res1)
        self.assertEqual(disk_count, get_disk_count(self.cp1.host.host, self.cp1.pool, self.newvm.disk))
        self.assertEqual(x_disk_count, get_disk_count(self.cp1.host.host, self.cp1.pool, 'x_'+self.newvm.disk))
        
        conn = libvirt.open("qemu+ssh://%s/system" % self.h1.ipv4)
        domain = conn.lookupByUUIDString(self.newvm.uuid)
        domain.destroy()
        
        #常规测试
        disk_count = get_disk_count(self.cp1.host.host, self.cp1.pool, self.newvm.disk)
        x_disk_count = get_disk_count(self.cp1.host.host, self.cp1.pool, 'x_'+self.newvm.disk)
        res2 = op({'req_user': self.u1, 'uuid': self.newvm.uuid, 'op': 'reset'})
        exp2 = {'res': True}
        self.assertDictEqual(exp2, res2)
        self.assertEqual(disk_count, get_disk_count(self.cp1.host.host, self.cp1.pool, self.newvm.disk))
        self.assertEqual(x_disk_count + 1, get_disk_count(self.cp1.host.host, self.cp1.pool, 'x_'+self.newvm.disk))
        
        
        
    def test_op_delete(self):
        if not self._setupvm():
            return
        
        res1 = op({'req_user': self.u1, 'uuid': self.newvm.uuid, 'op': 'delete'})
        exp1 = {'res': True}
        self.assertDictEqual(exp1, res1)
        
        #domain 是否删除
        r = self._vm_exist(self.h1.ipv4, self.newvm.uuid)
        self.assertFalse(r)
        
        # 虚拟机记录是否删除
        vmobj = Vm.objects.filter(uuid = self.newvm.uuid)
        self.assertFalse(vmobj.exists())
        
        # 归档记录是否添加
        vmarc = VmArchive.objects.filter(uuid = self.newvm.uuid)
        self.assert_(vmarc.exists())
        self.assert_(vmarc.count() == 1)
        
        # 归档记录是否正确
        if vmarc.count() == 1:
            vmarc = vmarc[0]
            self.assert_(vmarc.center_id == self.c1.id)
            self.assert_(vmarc.center_name == self.c1.name)
            self.assert_(vmarc.group_id == self.g1.id)
            self.assert_(vmarc.group_name == self.g1.name)
            self.assert_(vmarc.host_id == self.h1.id)
            self.assert_(vmarc.host_ipv4 == self.h1.ipv4)
            self.assert_(vmarc.ceph_host == self.cp1.host.host)
            self.assert_(vmarc.ceph_pool == self.cp1.pool)
            self.assert_(vmarc.image_id == self.i1.id)
            self.assert_(vmarc.image_snap == self.i1.snap)
            self.assert_(vmarc.name == self.newvm.name)
            self.assert_(vmarc.uuid == self.newvm.uuid)
            self.assert_(vmarc.vcpu == self.newvm.vcpu)
            self.assert_(vmarc.mem == self.newvm.mem)
            self.assert_(vmarc.disk[2:-21] == self.newvm.disk)
            self.assert_(vmarc.mac == self.ip1.mac)
            self.assert_(vmarc.ipv4 == self.ip1.ipv4)
            self.assert_(vmarc.vlan == self.v1.vlan)
            self.assert_(vmarc.br == self.v1.br)
            
            self.vm_disk = vmarc.disk
            
        # 宿主机信息是否正确
        host = Host.objects.get(pk = self.h1.pk)
        self.assert_(host.vcpu_total == self.h1.vcpu_total)
        self.assert_(host.vcpu_allocated == 0)
        self.assert_(host.mem_total == self.h1.mem_total)
        self.assert_(host.mem_allocated == 0)
        self.assert_(host.mem_reserved == self.h1.mem_reserved)
        self.assert_(host.vm_limit == self.h1.vm_limit)
        self.assert_(host.vm_created == 0) 
        
        # IP地址是否释放
        ip = MacIP.objects.get(pk = self.ip1.pk)
        self.assert_(ip.vmid == '')
        
    def test_edit_args(self):
        if not self._setupvm():
            return
        
        #参数缺失测试
        res1 = edit({})
        exp1 = {'res': False}
        self.assertDictContainsSubset(exp1, res1)
        
        res2 = edit({'req_user': self.u1})
        self.assertDictContainsSubset(exp1, res2)
        
        res3 = edit({'req_user': self.u1, 'uuid': self.newvm.uuid})
        self.assertDictContainsSubset(exp1, res3)
        
        #负数测试
        self.newvm = Vm.objects.get(pk = self.newvm.pk)
        vcpu = -3
        res8 = edit({'req_user': self.u1, 'uuid': self.newvm.uuid, 'vcpu': vcpu})
        self.assertDictContainsSubset(exp1, res8)
        
        mem = -2048
        res9 = edit({'req_user': self.u1, 'uuid': self.newvm.uuid, 'mem': mem})
        self.assertDictContainsSubset(exp1, res9)
        
        self._assert_vcpu_mem(self.newvm.vcpu, self.newvm.mem)

        #字符串测试
        self.newvm = Vm.objects.get(pk = self.newvm.pk)
        vcpu = 'abd'
        res8 = edit({'req_user': self.u1, 'uuid': self.newvm.uuid, 'vcpu': vcpu})
        self.assertDictContainsSubset(exp1, res8)
        
        mem = 'ab'
        res9 = edit({'req_user': self.u1, 'uuid': self.newvm.uuid, 'mem': mem})
        self.assertDictContainsSubset(exp1, res9)
        
        self._assert_vcpu_mem(self.newvm.vcpu, self.newvm.mem)
        
        #超额修改测试
        mem = 999999999
        res9 = edit({'req_user': self.u1, 'uuid': self.newvm.uuid, 'mem': mem})
        self.assertDictContainsSubset(exp1, res9)
        
        self._assert_vcpu_mem(self.newvm.vcpu, self.newvm.mem)
    
    def test_edit_remark(self):
        if not self._setupvm():
            return
        # 修改备注测试
        remarks = u'测试测试'
        res4 = edit({'req_user': self.u1, 'uuid': self.newvm.uuid, 'remarks': remarks})
        exp4 = {'res': True}
        self.assertDictEqual(exp4, res4)
        vmobj = Vm.objects.get(pk = self.newvm.pk)
        self.assert_(vmobj.remarks == remarks)    
        self._assert_vcpu_mem(self.newvm.vcpu, self.newvm.mem)
    
    def test_edit_when_running(self):
        if not self._setupvm():
            return
        #运行状态修改cpu或mem测试
        vcpu = 4
        res1 = edit({'req_user': self.u1, 'uuid': self.newvm.uuid, 'vcpu': vcpu})
        exp1 = {'res': False}
        self.assertDictContainsSubset(exp1, res1)
        
        self._assert_vcpu_mem(self.newvm.vcpu, self.newvm.mem)
        
    def test_edit(self):
        if not self._setupvm():
            return
        conn = libvirt.open("qemu+ssh://%s/system" % self.h1.ipv4)
        domain = conn.lookupByUUIDString(self.newvm.uuid)
        domain.destroy()
        
        #修改cpu测试
        self.newvm = Vm.objects.get(pk = self.newvm.pk)
        vcpu = 4
        res1 = edit({'req_user': self.u1, 'uuid': self.newvm.uuid, 'vcpu': vcpu})
        exp1 = {'res': True}
        self.assertDictEqual(exp1, res1)
        
        self._assert_vcpu_mem(vcpu, self.newvm.mem)
        
        #修改mem测试
        self.newvm = Vm.objects.get(pk = self.newvm.pk)
        mem = 4096
        res2 = edit({'req_user': self.u1, 'uuid': self.newvm.uuid, 'mem': mem})
        self.assertDictEqual(exp1, res2)
        
        self._assert_vcpu_mem(self.newvm.vcpu, mem)
        
        #修改cpu和mem测试
        self.newvm = Vm.objects.get(pk = self.newvm.pk)
        vcpu = 3
        mem = 3000
        res3 = edit({'req_user': self.u1, 'uuid': self.newvm.uuid, 'vcpu': vcpu, 'mem': mem})
        self.assertDictEqual(exp1, res3)
        
        self._assert_vcpu_mem(vcpu, mem)
        

        
    def _assert_vcpu_mem(self, vcpu, mem, num = 1):
        self._assert_vm(vcpu, mem)
        self._assert_host(self.h1, vcpu, mem, num)
    
    def _assert_vm(self, vcpu, mem):
        vmobj = Vm.objects.get(pk = self.newvm.pk)
        self.assert_(vmobj.vcpu == vcpu)
        self.assert_(vmobj.mem == mem)
        
    def _assert_host(self, host, vcpu, mem, num = 1):
        hostobj = Host.objects.get(pk = host.pk)
        self.assert_(hostobj.vcpu_total == host.vcpu_total)
        self.assert_(hostobj.vcpu_allocated == vcpu)
        self.assert_(hostobj.mem_total == host.mem_total)
        self.assert_(hostobj.mem_allocated == mem)
        self.assert_(hostobj.mem_reserved == host.mem_reserved)
        self.assert_(hostobj.vm_limit == host.vm_limit)
        self.assert_(hostobj.vm_created == num)
                      
class VmMigrateTest(TestCase):
    vcpu = 2
    mem = 2048
    def setUp(self):
        u1 = User()
        u1.username = u'apiuser'
        u1.is_active = True
        u1.api_user = True
        u1.save()
        self.u1 = u1
        
        u2 = User()
        u2.username = u'apiuser1'
        u2.is_active = True
        u2.api_user = True
        u2.save()
        self.u2 = u2

        u3 = User()
        u3.username = u'superuser'
        u3.is_active = True
        u3.api_user = True
        u3.is_superuser = True
        u3.save()
        self.u3 = u3

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
                
        vt1 = VlanType()
        vt1.code = u'vlantype1'
        vt1.name = u'vlantype1'
        vt1.save()
        self.vt1 = vt1
        
        v1 = Vlan()
        v1.vlan = unicode(TEST_VLAN)
        v1.br = unicode(TEST_BR)
        v1.type = vt1
        v1.enable = True
        v1.save()
        self.v1 = v1
        
        ip1 = MacIP()
        ip1.vlan = v1
        ip1.mac = TEST_MAC
        ip1.ipv4 = TEST_IP
        ip1.save()
        self.ip1 = ip1
                
        h1 = Host()
        h1.group = g1
        h1.ipv4 = unicode(TEST_HOST)
        h1.enable = True
        h1.save()
        h1.vlan.add(v1)
        self.h1 = h1
        
        h2 = Host()
        h2.group = g1
        h2.ipv4 = unicode(TEST_HOST_2)
        h2.enable = True
        h2.save()
        h2.vlan.add(v1)
        self.h2 = h2
        
        ch1 = CephHost()
        ch1.center = c1
        ch1.host = unicode(TEST_CEPH['host'])
        ch1.port = TEST_CEPH['port']
        ch1.uuid = unicode(TEST_CEPH['uuid'])
        ch1.save()
        
        cp1 = CephPool()
        cp1.host = ch1
        cp1.pool = TEST_CEPH['pool']
        cp1.type = 1
        cp1.save()
        self.cp1 = cp1
        
        it1 = ImageType()
        it1.code = u'code1'
        it1.name = u'imagetype1'
        it1.save()
        
        x1 = Xml()
        x1.name = u'linux'
        x1.xml = TEST_XML
        x1.save()
        
        i1 = Image()
        i1.cephpool = cp1
        i1.name = u'image1'
        i1.version = u'v0.1'
        i1.snap = TEST_IMAGE
        i1.desc = u''
        i1.xml = x1
        i1.type = it1
        i1.enable = True
        i1.save()
        self.i1 = i1
        
        self.vm_uuid = None
        self.vm_disk = None
        
    def tearDown(self):
#         print 'tear down ========================================'
        if self.vm_uuid:
            vmobj = Vm.objects.get(uuid = self.vm_uuid)
            if self._vm_exist(vmobj.host.ipv4, self.vm_uuid):
                cmd = 'ssh %s virsh destroy %s' % (vmobj.host.ipv4, self.vm_uuid)
                r, info = commands.getstatusoutput(cmd)
#                 if r != 0:
#                     os.system('ssh %s virsh destroy %s' % (self.h1.ipv4, self.vm_uuid))
#                     print info
                    
                cmd = 'ssh %s virsh undefine %s' % (vmobj.host.ipv4, self.vm_uuid)
                r, info = commands.getstatusoutput(cmd)
                if r != 0:
                    os.system('ssh %s virsh undefine %s' % (vmobj.host.ipv4, self.vm_uuid))
                    print info
                
            if not self.vm_disk:
                self.vm_disk  = 'test_'+self.vm_uuid
                
        if self.vm_disk:
            cmd = 'ssh %s rbd ls %s | grep x_%s' % (self.cp1.host.host, self.cp1.pool, self.vm_disk)
            r, info = commands.getstatusoutput(cmd)
            if r == 0:
                cmd1 = 'ssh %s rbd rm %s/x_%s' % (self.cp1.host.host, self.cp1.pool, self.vm_disk)
                r1, info1 = commands.getstatusoutput(cmd1)
                if r1 != 0:
                    os.system('ssh %s rbd rm %s/x_%s' % (self.cp1.host.host, self.cp1.pool, self.vm_disk))
                    print info1
                    
            cmd = 'ssh %s rbd ls %s | grep %s' % (self.cp1.host.host, self.cp1.pool, self.vm_disk)
            r, info = commands.getstatusoutput(cmd)
            if r == 0:
                cmd1 = 'ssh %s rbd rm %s/%s' % (self.cp1.host.host, self.cp1.pool, self.vm_disk)
                r1, info1 = commands.getstatusoutput(cmd1)
                if r1 != 0:
                    os.system('ssh %s rbd rm %s/%s' % (self.cp1.host.host, self.cp1.pool, self.vm_disk))
                    print info1
                
#         print 'finished tear down ================================'
    
    def _setupvm(self):
        res = create({'req_user': self.u1, 
                      'group_id': self.g1.id, 
                      'image_id': self.i1.id, 
                      'net_type_id': self.vt1.pk, 
                      'vcpu': self.vcpu, 
                      'mem': self.mem})
        if not res['res']:
            return False
        
        self.newvm = Vm.objects.get(uuid = res['uuid'])
        self.vm_uuid = self.newvm.uuid
        self.vm_disk = self.newvm.disk
        return True
      
        
    def _host_alive(self, ipv4):
        cmd = 'ping %s -c %d' % (ipv4, 3)
#         print cmd
        res, info = commands.getstatusoutput(cmd)
#         print info
        if res == 0:
            return True
        return False
    
    def _vm_exist(self, host_ip, vm_uuid):
        cmd = 'ssh %s virsh list --all | grep %s' % (host_ip, vm_uuid) 
        r, info = commands.getstatusoutput(cmd)
        if r == 0:
            return True
        return False

    def test_migrate_args(self):
        if not self._setupvm():
            return
        
        conn = libvirt.open("qemu+ssh://%s/system" % self.h1.ipv4)
        domain = conn.lookupByUUIDString(self.newvm.uuid)
        domain.destroy()
        
        res1 = migrate({})
        exp1 = {'res': False}
        self.assertDictContainsSubset(exp1, res1)
        
        res2 = migrate({'req_user': self.u1})
        self.assertDictContainsSubset(exp1, res2)
        
        res3 = migrate({'req_user': self.u1, 'uuid': self.newvm.uuid})
        self.assertDictContainsSubset(exp1, res3)
        
        res4 = migrate({'req_user': self.u1, 'host_id': self.h2.id})
        self.assertDictContainsSubset(exp1, res4)
    
    def test_migrate_when_running(self):
        if not self._setupvm():
            return
        
        if self.newvm.host == self.h1:
            target_host = self.h2
        else:
            target_host = self.h1
        res1 = migrate({'req_user': self.u1, 'uuid': self.newvm.uuid, 'host_id': target_host})
        exp1 = {'res': False}
        self.assertDictContainsSubset(exp1, res1)
    
    def test_migrate_same_host(self):
        if not self._setupvm():
            return
        
        conn = libvirt.open("qemu+ssh://%s/system" % self.h1.ipv4)
        domain = conn.lookupByUUIDString(self.newvm.uuid)
        domain.destroy()
        
        res1 = migrate({'req_user': self.u1, 'uuid': self.newvm.uuid, 'host_id': self.newvm.host.id})
        exp1 = {'res': False}
        self.assertDictContainsSubset(exp1, res1)
        
    def test_migrate(self):
        if not self._setupvm():
            return 
        
        conn = libvirt.open("qemu+ssh://%s/system" % self.h1.ipv4)
        domain = conn.lookupByUUIDString(self.newvm.uuid)
        domain.destroy()
        
        if self.newvm.host == self.h1:
            target_host = self.h2
        else:
            target_host = self.h1
        res1 = migrate({'req_user': self.u1, 'uuid': self.newvm.uuid, 'host_id': target_host})
        exp1 = {'res': True}
        self.assertDictEqual(exp1, res1)
        
        vmobj = Vm.objects.get(pk = self.newvm.pk)
        self.assert_(vmobj.host == target_host)
        
        self._assert_host(self.newvm.host, 0,0,0)
        self._assert_host(target_host, self.newvm.vcpu, self.newvm.mem, 1)
        
        
        
    def _assert_vcpu_mem(self, vcpu, mem, num = 1):
        self._assert_vm(vcpu, mem)
        self._assert_host(self.h1, vcpu, mem, num)
    
    def _assert_vm(self, vcpu, mem):
        vmobj = Vm.objects.get(pk = self.newvm.pk)
        self.assert_(vmobj.vcpu == vcpu)
        self.assert_(vmobj.mem == mem)
        
    def _assert_host(self, host, vcpu, mem, num = 1):
        hostobj = Host.objects.get(pk = host.pk)
        self.assert_(hostobj.vcpu_total == host.vcpu_total)
        self.assert_(hostobj.vcpu_allocated == vcpu)
        self.assert_(hostobj.mem_total == host.mem_total)
        self.assert_(hostobj.mem_allocated == mem)
        self.assert_(hostobj.mem_reserved == host.mem_reserved)
        self.assert_(hostobj.vm_limit == host.vm_limit)
        self.assert_(hostobj.vm_created == num)
                      
        
        
        
        
        