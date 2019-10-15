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
            raise NetworkError(msg=f'查询镜像时错误,{str(e)}')


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

