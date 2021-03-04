from django.contrib import admin

from .models import CephPool, CephCluster


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
