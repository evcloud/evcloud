from django.contrib import admin

from .models import Vlan, MacIP, NetworkType


@admin.register(Vlan)
class VlanAdmin(admin.ModelAdmin):
    list_display_links = ('name',)
    list_display = ('id', 'name', 'br', 'net_type', 'tag', 'enable', 'center', 'subnet_ip', 'net_mask', 'gateway', 'dns_server')
    list_filter = ('enable', 'net_type', 'tag')
    search_fields = ('name', 'br')
    list_select_related = ('net_type', 'center')


@admin.register(MacIP)
class MacIPAdmin(admin.ModelAdmin):
    list_display_links = ('id', 'ipv4',)
    list_display = ('id', 'ipv4', 'mac', 'vlan', 'enable', 'used', 'desc')
    list_filter = ('vlan', 'enable')
    search_fields = ('ipv4',)
    list_select_related = ('vlan',)


@admin.register(NetworkType)
class NetworkTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'remarks')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
