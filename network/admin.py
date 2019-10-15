from django.contrib import admin

from .models import Vlan, MacIP, NetworkType

# Register your models here.

@admin.register(Vlan)
class VlanAdmin(admin.ModelAdmin):
    list_display_links = ('name',)
    list_display = ( 'id', 'name', 'br', 'net_type', 'enable', 'subnet_ip', 'net_mask', 'gateway', 'dns_server')
    list_filter = ['enable', 'net_type']
    search_fields = ['name', 'br']


@admin.register(MacIP)
class MacIPAdmin(admin.ModelAdmin):
    list_display_links = ('id', 'ipv4',)
    list_display = ( 'id', 'ipv4', 'mac', 'vlan', 'enable', 'used', 'desc')
    list_filter = ['vlan', 'enable']
    search_fields = ['ipv4',]


@admin.register(NetworkType)
class NetworkTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'remarks')
    list_display_links = ( 'id', 'name')
    search_fields = ['name',]
