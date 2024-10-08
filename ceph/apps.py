from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CephConfig(AppConfig):
    name = 'ceph'
    verbose_name = _('全局配置')

    def ready(self):
        # 服务启动后的ceph初始化的操作
        self.setup_global_config()

    @staticmethod
    def setup_global_config():

        from ceph.models import GlobalConfig
        try:
            GlobalConfig().get_global_config()
        except Exception as e:
            pass
        return

