#coding=utf-8
#@author:   hai #@email:   zhhaim@qq.cn #@date:     2019-10-16
#@desc:    novnc token管理模块。完成读写novnc的token配置文件到数据库			

import os, uuid
import datetime
from django.conf import settings
from .models import Token

class NovncError(Exception):
    '''
    网络错误类型定义
    '''
    def __init__(self, code:int=0, msg:str='', err=None):
        '''
        :param code: 错误码
        :param msg: 错误信息
        :param err: 错误对象
        '''
        self.code = code
        self.msg = msg
        self.err = err

    def __str__(self):
        return self.detail()

    def detail(self):
        '''错误详情'''
        if self.msg:
            return self.msg

        if self.err:
            return str(self.err)

        return '未知的错误'

class NovncTokenManager(object):
    def generate_token(self, vmid, hostip):
        vncport = get_vm_vncinfo(vmid, hostip)
        #删除该hostip和vncport的历史token记录
        Token.objects.filter(ip = hostip).filter(port = vncport).delete()
        #创建新的token记录
        novnc_token = str(uuid.uuid4())
        new_token = Token.objects.create(token = novnc_token, ip = hostip, port = vncport)
        new_token.save();
        #删除 一年前 到 3天前 之间的token记录
        now = datetime.datetime.now()
        start_time = now - datetime.timedelta(days=365);   #print(start_time);
        end_time   = now - datetime.timedelta(days=3);     #print(end_time);
        Token.objects.filter(updatetime__range=(start_time, end_time)).delete();   #注意 __range表示范围
        return(f"/novnc/?vncid={novnc_token}")
    def del_token(self, vncid):
        Token.objects.filter(token = str(vncid)).delete()
    def get_vm_vncinfo(self, vmid, hostip):
        cmd = f'ssh {hostip} virsh vncdisplay {vmid}'
        (res, info) = subprocess.getstatusoutput(cmd)
        if res != 0:
            self.error = 'UUID error' 
            retrun False 
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
        return(vncport)    

