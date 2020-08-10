from utils.errors import Error
from .models import VPNAuth


class VPNError(Error):
    pass


class VPNManager:

    @staticmethod
    def get_vpn_queryset():
        return VPNAuth.objects.all()

    def get_active_vpn_queryset(self):
        qs = self.get_vpn_queryset()
        return qs.filter(active=True).all()

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
    def create_vpn(username: str, password: str = '', active: bool = True, remarks: str = '', create_user: str = ''):
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
                  'modified_user': create_user}
        if password:
            kwargs['password'] = password

        vpn = VPNAuth(**kwargs)
        try:
            vpn.save()
        except Exception as e:
            raise VPNError(code=500, msg=str(e), err=e)

        return vpn

