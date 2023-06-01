from django.contrib import admin

from .models import Vlan, MacIP


@admin.register(Vlan)
class VlanAdmin(admin.ModelAdmin):
    list_display_links = ('name',)
    list_display = ('id', 'br', 'vlan_id', 'name', 'tag', 'enable', 'group', 'subnet_ip', 'net_mask', 'gateway', 'dns_server')
    list_filter = ('enable', 'tag')
    search_fields = ('name', 'br', 'vlan_id')
    list_select_related = ('group',)


@admin.register(MacIP)
class MacIPAdmin(admin.ModelAdmin):
    list_display_links = ('id', 'ipv4',)
    list_display = ('id', 'ip_vm', 'ipv4', 'mac', 'vlan', 'enable', 'used', 'desc')
    list_filter = ('vlan', 'enable')
    search_fields = ('ipv4',)
    list_select_related = ('vlan',)
