from django.contrib import admin
from .models import VPNAuth, VPNConfig, VPNLog


@admin.register(VPNAuth)
class VPNAuthAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'password', 'active', 'create_time', 'expired_time', 'create_user',
                    'modified_time',
                    'modified_user', 'remarks']
    list_display_links = ['id', 'username']
    search_fields = ['username', 'remarks']


@admin.register(VPNConfig)
class VPNConfigAdmin(admin.ModelAdmin):
    list_display = ['id', 'tag', 'filename', 'modified_time']


@admin.register(VPNLog)
class VPNLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'timeunix', 'server_local_ip', 'client_ip', 'client_trusted_ip',
                    'client_trusted_port', 'bytes_received', 'bytes_sent', 'login_time', 'logout_time', ]

    search_fields = ['username', 'timeunix', 'server_local_ip', 'client_ip', 'client_trusted_ip']
