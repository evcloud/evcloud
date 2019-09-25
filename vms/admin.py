from django.contrib import admin

from .models import (Center, CephBackend, CephConfig, Group, Host, Vlan, MacIP, VmXmlTemplate, Image, ImageType, Vm)
# Register your models here.

@admin.register(CephConfig)
class CephConfigAdmin(admin.ModelAdmin):
    list_display_links = ('name',)
    list_display = ( 'id', 'name', 'uuid', 'config_file','keyring_file', 'hosts_xml', 'username')
    # list_filter = ['name']
    search_fields = ['name', 'hosts_xml']


@admin.register(CephBackend)
class CephBackendAdmin(admin.ModelAdmin):
    list_display_links = ('id', 'pool_name')
    list_display = ( 'id', 'pool_name', 'ceph')
    # list_filter = ['ceph']
    # search_fields = ['pool_name']


@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    list_display_links = ('name',)
    list_display = ( 'id', 'name', 'location', 'desc','backends_list')
    list_filter = ['location']
    search_fields = ['name', 'location']
    filter_horizontal = ['backends']

    # 显示多对多字段, 定义一个方法，遍历，然后用列表返回
    # Field producer_country
    def backends_list(self, obj):
        return [str(item) for item in obj.backends.all()]
    backends_list.short_description = '存储后端'  # admin后台此字段表列显示名称，等价于模型字段verbose_name参数


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


@admin.register(Vlan)
class VlanAdmin(admin.ModelAdmin):
    list_display_links = ('name',)
    list_display = ( 'id', 'name', 'br', 'type', 'enable', 'subnet_ip', 'net_mask', 'gateway', 'dns_server')
    list_filter = ['enable', 'type']
    search_fields = ['name', 'br']


@admin.register(MacIP)
class MacIPAdmin(admin.ModelAdmin):
    list_display_links = ('id', 'ipv4',)
    list_display = ( 'id', 'ipv4', 'mac', 'vlan', 'enable', 'desc')
    list_filter = ['vlan', 'enable']
    search_fields = ['ipv4',]


@admin.register(VmXmlTemplate)
class VmXmlTemplateAdmin(admin.ModelAdmin):
    list_display_links = ('id', 'name',)
    list_display = ( 'id', 'name', 'desc')
    search_fields = ['name', 'desc']


@admin.register(ImageType)
class ImageTypeAdmin(admin.ModelAdmin):
    list_display_links = ('id', 'name',)
    list_display = ( 'id', 'name')
    search_fields = ['name',]


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display_links = ('id', 'name',)
    list_display = ( 'id', 'name', 'version', 'type', 'enable', 'xml_tpl', 'desc')
    search_fields = ['name',]
    list_filter = ['type', 'enable']


@admin.register(Vm)
class VmAdmin(admin.ModelAdmin):
    list_display_links = ('uuid', 'name',)
    list_display = ( 'uuid', 'name', 'mac_ip', 'vcpu', 'mem', 'host', 'user', 'create_time', 'remarks')
    search_fields = ['name','mac_ip__name']
    list_filter = ['host', 'user']

