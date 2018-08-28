#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2015-10-19
#@desc:    vnc            
########################################################################
import os, uuid
import subprocess
from compute.models import Vm
from compute.vm.vm import VM, VIR_DOMAIN_RUNNING
from django.conf import settings
from .token import TokenManager
import cmd

class VNC():
    instance = TokenManager.instance
    def set_token(self, vmid):
        '''设置novnc token, 并返回vncid'''
        obj = Vm.objects.filter(uuid = vmid)
        if obj:
            obj = obj[0]
        else:
            self.error = 'UUID error.'
            return False
    
        vm = VM(obj)
    
        
        cmd = 'ssh %s virsh vncdisplay %s'%(obj.host.ipv4, obj.uuid)
        (res, info) = subprocess.getstatusoutput(cmd)
        if res == 0:
            port = False
            for line in info.split('\n'):
                line = line.strip()
                if len(line) > 0 and line[0] == ':':
                    if line[1:].isdigit():
                        port = settings.VNCSERVER_BASE_PORT + int(line[1:])
                        break
            if port == False:
                self.error = 'get vnc port error.'
                return False
            vncid = uuid.uuid4()    
            self.instance.add_token(vncid, obj.host.ipv4, port)    
            return {
                'url':'/vnc/?vncid=%(vncid)s' % {
                    'vncid': vncid
                    },
                'id':vncid
                }
        self.error = 'vnc server error.'
        return False
    
    def del_token(self, vncid):
        vncid = str(vncid)
        self.instance.del_token(vncid)