from ceph.models import GlobalConfig
from utils.errors import VPNError
from .models import VPNAuth, VPNLog


class VPNManager:

    @staticmethod
    def get_vpn_queryset():
        return VPNAuth.objects.all()

    def get_active_vpn_queryset(self):
        qs = self.get_vpn_queryset()
        return qs.filter(active=True).all()

    def get_unactive_vpn_queryset(self):
        qs = self.get_vpn_queryset()
        return qs.filter(active=False).all()

    def get_vpn(self, username: str):
        """
        :return:
            VPNAuth()       # exists
            None            # not exists
        """
        qs = self.get_vpn_queryset()
        return qs.filter(username=username).first()

    def get_vpn_by_id(self, pk: int):
        """
        :return:
            VPNAuth()       # exists
            None            # not exists
        """
        qs = self.get_vpn_queryset()
        return qs.filter(id=pk).first()

    @staticmethod
    def create_vpn(username: str, password: str = '', expired_time = None, active: bool = True, remarks: str = '', create_user: str = ''):
        """
        :param username: 用户名
        :param password: 密码口令
        :param active: 激活状态；默认激活
        :param remarks: 备注信息
        :param create_user: 创建用户名
        :return:
            VPNAuth()

        :raises: VPNError
        """
        kwargs = {'username': username, 'remarks': remarks, 'active': active, 'create_user': create_user,
                  'modified_user': create_user, 'expired_time': expired_time}
        if password:
            kwargs['password'] = password

        vpn = VPNAuth(**kwargs)
        try:
            vpn.save()
        except Exception as e:
            raise VPNError(code=500, msg=str(e), err=e)

        return vpn

    @staticmethod
    def vpn_config_file():
        """
        vpn配置文件元数据
        :return:
            None or GlobalConfig()
        """

        return GlobalConfig.objects.filter(name='vpnUserConfig').first()

    @staticmethod
    def vpn_ca_file():
        """
        vpn ca证书元数据
        :return:
            None or GlobalConfig()
        """
        return GlobalConfig.objects.filter(name='vpnUserConfigCA').first()

    def vpn_login_num(self):
        """vpn 登录数"""
        return VPNLog.objects.filter(logout_time=None).count()
