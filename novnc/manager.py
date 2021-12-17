# coding=utf-8
# @author:   hai #@email:   zhhaim@qq.cn #@date:     2019-10-16
# @desc:    novnc token管理模块。完成读写novnc的token配置文件到数据库

import uuid
import subprocess

from django.conf import settings
from django.utils import timezone

from .models import Token
from utils.errors import NovncError


class NovncTokenManager(object):
    def generate_token(self, vmid: str, hostip: str):
        """
        创建虚拟机vnc url

        :param vmid:
        :param hostip:
        :return:
            (vnc_id:str, vnc_url:str)   # success

        :raise: NovncError
        """
        protocol_type, port = self.get_vm_graphics_info(vmid, hostip)
        port = str(port)
        now = timezone.now()
        # 删除该hostip和vncport的历史token记录
        Token.objects.filter(ip=hostip, port=port, expiretime__lt=now).delete()
        # 创建新的token记录
        token = str(uuid.uuid4())
        Token.objects.create(token=token, ip=hostip, port=port, expiretime=now)
 
        # 删除（一年前 到 3天前）之间有更新的，现在过期的所有token记录
        start_time = now - timezone.timedelta(days=365)     # print(start_time);
        end_time = now - timezone.timedelta(days=3)         # print(end_time);
        Token.objects.filter(updatetime__range=(start_time, end_time)).filter(expiretime__lt=now).delete()
        return token, f"/novnc/?vncid={token}&type={protocol_type}"

    @staticmethod
    def del_token(vncid):
        Token.objects.filter(token=str(vncid)).delete()

    @staticmethod
    def get_vm_graphics_info(vmid, hostip):
        """
        获取虚拟机的graphics display

        :param vmid:
        :param hostip:
        :return:
            (
                protocol_type: str  # vnc or spice
                port: int           # post
            )
        :raise: NovncError
        """
        # spice[vnc]://localhost:5910 ; spice://127.0.0.1?tls-port=5910
        cmd = f'ssh {hostip} virsh domdisplay {vmid}'
        # cmd = f'ssh {hostip} virsh vncdisplay {vmid}'
        res, info = subprocess.getstatusoutput(cmd)
        if res != 0:
            raise NovncError(msg=info)

        protocol_type = ''
        port = False
        for line in info.split('\n'):
            line = line.strip()
            if line.startswith('spice') or line.startswith('vnc'):
                protocol_type, line = line.split('://')
                if 'tls-port' in line:
                    _, port = line.split('tls-port=')
                else:
                    _, port = line.split(':')

                if port.isdigit():
                    if protocol_type == 'spice':
                        port = int(port)
                    else:
                        port = settings.VNCSERVER_BASE_PORT + int(port)

                    break

        if not port:
            raise NovncError(msg='Get graphics display info failed.')

        return protocol_type, port
