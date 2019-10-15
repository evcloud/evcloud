from django.contrib import admin

from .models import Center, Group, Host

# Register your models here.

@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    list_display_links = ('name',)
    list_display = ( 'id', 'name', 'location', 'desc','ceph_clusters_list')
    list_filter = ['location']
    search_fields = ['name', 'location']

    # 显示多对多字段, 定义一个方法，遍历，然后用列表返回
    # Field producer_country
    def ceph_clusters_list(self, obj):
        return [str(item) for item in obj.ceph_clusters.all()]
    ceph_clusters_list.short_description = 'CEPH集群'  # admin后台此字段表列显示名称，等价于模型字段verbose_name参数


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display_links = ('name',)
    list_display = ( 'id', 'name', 'center', 'desc')
    list_filter = ['center']
    search_fields = ['name']
    filter_horizontal = ['users']


@admin.register(Host)
class HostAdmin(admin.ModelAdmin):
    list_display_links = ('ipv4',)
    list_display = ( 'id', 'ipv4', 'group', 'vcpu_total', 'vcpu_allocated', 'mem_total', 'mem_allocated', 'vm_created', 'enable')
    list_filter = ['group']
    search_fields = ['ipv4']
    filter_horizontal = ['vlans']
