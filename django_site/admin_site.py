from django.contrib import admin
from django.contrib.admin.models import LogEntry
from rest_framework.authtoken.admin import TokenAdmin
from django.conf import settings

ADMIN_SORTED_APP_LIST = settings.ADMIN_SORTED_APP_LIST

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
    admin.AdminSite.get_app_list = get_app_list  # 覆盖原有的get_app_list方法
    config_token_admin()


def get_app_list(self, request, app_label=None):
    """
    Return a sorted list of all the installed apps that have been
    registered in this site.
    """
    app_dict = self._build_app_dict(request, app_label)

    # Sort the apps alphabetically.
    # app_list = sorted(app_dict.values(), key=lambda x: x["name"].lower())

    # 如果应用标签(如app1, app2, 在ADMIN_SORTED_APP_LIST中，则按其索引排， 否则排最后面
    app_count = len(ADMIN_SORTED_APP_LIST)  # 获取app数量
    app_list = sorted(
        app_dict.values(),
        key=lambda x: ADMIN_SORTED_APP_LIST.index(
            x['app_label']) if x['app_label'] in ADMIN_SORTED_APP_LIST else app_count
    )
    default_priority=100
    # Sort the models alphabetically within each app.
    for app in app_list:
        model_order = {}
        try:
            for model in app['models']:
                from django.contrib.admin.sites import site
                from django.apps import apps

                model_order[model['object_name']] = getattr(
                    site._registry[apps.get_model(app['app_label'], model['object_name'])],
                    'admin_order',
                    default_priority
                )
            app['models'].sort(key=lambda model_: model_order[model_['object_name']])
        except Exception as e:
            app["models"].sort(key=lambda x: x["name"])

    return app_list

config_site()
