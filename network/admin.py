from django.contrib import admin

from .models import Vlan, MacIP

# Register your models here.

@admin.register(Vlan)
class VlanAdmin(admin.ModelAdmin):
    list_display_links = ('name',)
    list_display = ( 'id', 'name', 'br', 'type', 'enable', 'subnet_ip', 'net_mask', 'gateway', 'dns_server')
    list_filter = ['enable', 'type']
    search_fields = ['name', 'br']


@admin.register(MacIP)
class MacIPAdmin(admin.ModelAdmin):
    list_display_links = ('id', 'ipv4',)
    list_display = ( 'id', 'ipv4', 'mac', 'vlan', 'enable', 'used', 'desc')
    list_filter = ['vlan', 'enable']
    search_fields = ['ipv4',]
