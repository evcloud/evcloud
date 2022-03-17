from django.contrib import admin
from django.contrib.admin.models import LogEntry
from rest_framework.authtoken.admin import TokenAdmin


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'content_type', 'object_repr', 'action_flag', 'get_change_message')
    search_fields = ('user__username',)  # 搜索字段

    def get_change_message(self, obj):
        return obj.get_change_message()


def config_token_admin():
    search_fields = ['user__username',]
    if TokenAdmin.search_fields:
        search_fields += list(TokenAdmin.search_fields)

    TokenAdmin.search_fields = search_fields


def config_site():
    admin.AdminSite.site_header = 'EVCloud后台管理（管理员登录）'
    admin.AdminSite.site_title = '管理员登录'
    config_token_admin()


config_site()
