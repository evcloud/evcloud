import re
from io import StringIO

from django.db import transaction

from .models import Vlan, MacIP


class NetworkError(Exception):
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


class VlanManager:
    '''
    局域子网Vlan管理器
    '''
    def get_vlan_by_id(self, vlan_id:int):
        '''
        通过id获取镜像元数据模型对象
        :param vlan_id: 镜像id
        :return:
            Vlan() # success
            None    #不存在

        :raise NetworkError
        '''
        if not isinstance(vlan_id, int) or vlan_id < 0:
            raise NetworkError(msg='子网ID参数有误')

        try:
            return Vlan.objects.filter(id=vlan_id).first()
        except Exception as e:
            raise NetworkError(msg=f'查询子网时错误,{str(e)}')

    def get_vlan_queryset(self):
        return Vlan.objects.filter(enable=True).all()

    def generate_subips(self, vlan_id, from_ip, to_ip, write_database=False):
        '''
        生成子网ip
        :param vlan_id:
        :param from_ip: 开始ip
        :param to_ip: 结束ip
        :param write_database: True 生成并导入到数据库 False 生成不导入数据库
        :return:
        '''
        reg = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        if not (re.match(reg, from_ip) and re.match(reg, to_ip)):
            raise NetworkError(msg='输入的ip地址错误')
        ip_int = [[*map(int, ip.split('.'))] for ip in (from_ip, to_ip)]
        ip_hex = [ip[0] << 24 | ip[1] << 16 | ip[2] << 8 | ip[3] for ip in ip_int]
        if ip_hex[0] > ip_hex[1]:
            raise NetworkError(msg='输入的ip地址错误')

        subips = [f'{ip >> 24}.{(ip & 0x00ff0000) >> 16}.{(ip & 0x0000ff00) >> 8}.{ip & 0x000000ff}'
                  for ip in range(ip_hex[0], ip_hex[1] + 1) if ip & 0xff]
        submacs = ['C8:00:' + ':'.join(map(lambda x: x[2:].upper().rjust(2, '0'), map(lambda x: hex(int(x)), ip.split('.'))))
                   for ip in subips]
        if write_database:
            with transaction.atomic():
                for subip, submac in zip(subips, submacs):
                    try:
                        MacIP.objects.create(vlan_id=vlan_id, ipv4=subip, mac=submac)
                    except Exception as error:
                        raise NetworkError(msg='ip写入数据库失败，部分ip数据库中已有')

        return [*zip(subips, submacs)]

    def get_macips_by_vlan(self, vlan):
        '''
        获得vlan对应的所有macip记录
        :param vlan:
        :return: 直接返回查询结果
        '''
        try:
            macips = MacIP.objects.filter(vlan=vlan)
        except Exception as error:
            raise NetworkError(msg='读取macips失败。' + str(error))
        return macips

    def generate_config_file(self, vlan, macips):
        '''
        生成DHCP配置文件
        :param vlan: vlan对象
        :param macips: 对应vlan下的所有macip组
        :return: 返回文件数据
        '''
        lines = 'subnet %s netmask %s {\n' % (vlan.subnet_ip, vlan.net_mask)
        lines += '\t' + 'option routers\t%s;\n' % vlan.gateway
        lines += '\t' + 'option subnet-mask\t%s;\n' % vlan.net_mask
        lines += '\t' + 'option domain-name-servers\t%s;\n' % vlan.dns_server
        lines += '\t' + vlan.dhcp_config + '\n'
        # lines = lines + '\t' + 'option domain-name-servers\t8.8.8.8;\n'
        # lines = lines + '\t' + 'option time-offset\t-18000; # EAstern Standard Time\n'
        # lines = lines + '\t' + 'range dynamic-bootp 10.0.224.240 10.0.224.250;\n'
        # lines = lines + '\t' + 'default-lease-time 21600;\n'
        # lines = lines + '\t' + 'max-lease-time 43200;\n'
        # lines = lines + '\t' + 'next-server 159.226.50.246;   #tftp server\n'
        # lines = lines + '\t' + 'filename "/pxelinux.0";    #boot file\n'

        for macip in macips:
            lines += '\t' + 'host %s{hardware ethernet %s;fixed-address %s;}\n' % ('v_' + macip.ipv4.replace('.', '_'), macip.mac, macip.ipv4)
        return vlan.subnet_ip + '_dhcpd.conf', StringIO(lines)


class MacIPManager:
    '''
    mac ip地址管理器
    '''
    def get_macip_by_id(self, macip_id:int):
        '''
        通过id获取mac ip

        :param macip_id: mac ip id
        :return:
            MacIP() # success
            None    #不存在

        :raise NetworkError
        '''
        if not isinstance(macip_id, int) or macip_id < 0:
            raise NetworkError(msg='MacIP ID参数有误')

        try:
            return MacIP.objects.filter(id=macip_id).first()
        except Exception as e:
            raise NetworkError(msg=f'查询MacIP时错误,{str(e)}')

    def has_free_ip_in_vlan(self, vlan_id:int):
        '''
        子网中是否有可用的IP

        :param vlan_id: 子网id
        :return:
            True: 有
            False: 没有
        '''
        qs = MacIP.get_all_free_ip_in_vlan(vlan_id)
        if qs.count() > 0:
            return True

        return False

    def apply_for_free_ip(self, vlan_id:int, ipv4:str=''):
        '''
        申请一个未使用的ip，申请成功的ip不再使用时需要通过free_used_ip()释放

        :param vlan_id: 子网id
        :param ipv4: 指定要申请的ip
        :return:
            MacIP() # 成功
            None    # 失败
        '''
        with transaction.atomic():
            qs_ips = MacIP.objects.select_for_update().filter(vlan=vlan_id, used=False, enable=True)
            if ipv4:
                qs_ips = qs_ips.filter(ipv4=ipv4)

            ip = qs_ips.first()
            if not ip:
                return None

            ip.used = True
            ip.save()

        return ip

    def free_used_ip(self, ip_id:int=0, ipv4:str=''):
        '''
        释放一个使用中的ip,通过id或ip

        :param ip_id:
        :param ipv1:
        :return:
            True    # success
            False   # failed
        '''
        with transaction.atomic():
            if ip_id > 0:
                ip = MacIP.objects.select_for_update().filter(id=ip_id).first()
            elif ipv4:
                ip = MacIP.objects.select_for_update().filter(ipv4=ipv4).first()
            else:
                return False

            if not ip:
                return False

            if not ip.set_free():
                return False
        return True

