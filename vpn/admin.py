from django.contrib import admin
from .models import VPNAuth, VPNConfig


@admin.register(VPNAuth)
class VPNAuthAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'password', 'active', 'create_time', 'expired_time', 'create_user', 'modified_time',
                    'modified_user', 'remarks']
    list_display_links = ['id', 'username']
    search_fields = ['username', 'remarks']


@admin.register(VPNConfig)
class VPNConfigAdmin(admin.ModelAdmin):
    list_display = ['id', 'tag', 'filename', 'modified_time']
