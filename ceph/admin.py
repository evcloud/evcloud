from django.contrib import admin

from .models import CephPool, CephCluster
from .models import CephPool, CephCluster, GlobalConfig


@admin.register(CephCluster)
class CephClusterAdmin(admin.ModelAdmin):
    list_display_links = ('name',)
    list_display = ('id', 'name', 'has_auth', 'uuid', 'config_file', 'keyring_file', 'hosts_xml', 'username')
    # list_filter = ['name']
    search_fields = ['name', 'hosts_xml']


@admin.register(CephPool)
class CephPoolAdmin(admin.ModelAdmin):
    list_display_links = ('id', 'pool_name')
    list_display = ('id', 'pool_name', 'has_data_pool', 'data_pool', 'ceph', 'remarks')
    # list_filter = ['ceph']
    # search_fields = ['pool_name']


@admin.register(GlobalConfig)
class GlobalConfigTableAdmin(admin.ModelAdmin):
    list_display_links = ('id',)
    list_display = ('id', 'name', 'content', 'remark', 'create_time', 'modif_time')

    # def has_delete_permission(self, request, obj=None):
    #     return False
    #
    # def has_add_permission(self, request):
    #     is_exist = GlobalConfig.objects.first()
    #     if is_exist:
    #         return False
    #
    #     return super().has_add_permission(request=request)
