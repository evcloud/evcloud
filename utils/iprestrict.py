import ipaddress
from collections import namedtuple
from typing import List, Union

from django.conf import settings
from django.utils.translation import gettext as _

from utils import errors

IPRange = namedtuple('IPRange', ['start', 'end'])


def convert_iprange(ip_str: str) -> Union[ipaddress.IPv4Network, IPRange]:
    if '/' in ip_str:
        try:
            return ipaddress.IPv4Network(ip_str, strict=False)
        except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
            raise Exception(_('无效的IP子网'))
    elif '-' in ip_str:
        items = ip_str.split('-')
        if len(items) != 2:
            raise Exception(_('无效的IP网段'))

        start = items[0].strip(' ')
        end = items[1].strip(' ')
        try:
            start = ipaddress.IPv4Address(start)
            end = ipaddress.IPv4Address(end)
            if end >= start:
                return IPRange(start=start, end=end)

            raise Exception(_('无效的IP网段，地址无效'))
        except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
            raise Exception(_('无效的IP网段，地址无效'))
    else:
        try:
            start = ipaddress.IPv4Address(ip_str)
            return IPRange(start=start, end=start)
        except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
            raise Exception(_('无效的IP地址'))


def load_allowed_ips(setting_key: str) -> List[Union[ipaddress.IPv4Network, IPRange]]:
    ips = getattr(settings, setting_key, [])
    allowed_ips = []
    for ip_str in ips:
        if not isinstance(ip_str, str):
            continue

        try:
            allowed_ips.append(convert_iprange(ip_str))
        except Exception:
            pass

    return allowed_ips


class IPRestrictor:
    _allowed_ip_rules = []

    def reload_ip_rules(self):
        raise NotImplementedError('继承类IPRestrictor的子类没有实现类方法“reload_ip_rules”')

    @property
    def allowed_ips(self):
        return self._allowed_ip_rules

    @allowed_ips.setter
    def allowed_ips(self, ips: list):
        for i in ips:
            if not isinstance(i, IPRange) and not isinstance(i, ipaddress.IPv4Network):
                raise ValueError('IP列表数据项类型必须是“IPv4Network”或者“IPRange”')

        self._allowed_ip_rules = ips

    def check_restricted(self, request):
        """
        :return:
            ip: str
        :raises: AccessDenied
        """
        client_ip, proxy_ips = self.get_remote_ip(request)
        self.is_restricted(client_ip=client_ip)
        return client_ip

    def is_restricted(self, client_ip: str):
        """
        鉴权客户端ip是否拒绝访问

        :return: False  # 允许访问
        :raises: AccessDenied   # 拒绝访问
        """
        try:
            client_ip = ipaddress.IPv4Address(client_ip)
        except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
            raise errors.AccessDeniedError(msg=_('无法获取到有效的客户端IPv4地址。') + client_ip)

        for ip_rule in self.allowed_ips:
            if isinstance(ip_rule, IPRange):
                if ip_rule.start <= client_ip <= ip_rule.end:
                    return False
            else:
                if client_ip in ip_rule:
                    return False

        raise errors.AccessDeniedError(msg=_("此API拒绝从IP地址'%s'访问") % (client_ip,))

    @staticmethod
    def get_remote_ip(request):
        """
        获取客户端的ip地址和代理ip

            X-Forwarded-For 可能伪造，需要在服务一级代理防范处理
            比如nginx：
            uwsgi_param X-Forwarded-For $remote_addr;     不能使用 $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-For $remote_addr;     不能使用 $proxy_add_x_forwarded_for;

        :return: (
            str,    # 客户端真实ip地址
            list    # 经过的代理ip地址列表
        )
        """
        if 'X-Forwarded-For' in request.META:
            h = request.META.get('X-Forwarded-For')
        elif 'HTTP_X-Forwarded-For' in request.META:
            h = request.META.get('HTTP_X-Forwarded-For')
        else:
            # 标头 X-Forwarded-For 不存在
            # 没有经过代理时， REMOTE_ADDR是客户端地址
            # 经过代理时，socket方式时， REMOTE_ADDR是客户端地址；http方式时，REMOTE_ADDR是代理地址（如果代理到本机，获取的ip可能是127.0.0.1）
            return request.META.get('REMOTE_ADDR', ''), []

        ips = h.split(',')
        ips = [i.strip(' ') for i in ips]
        return ips.pop(0), ips
