from django.contrib import admin

from .models import Vlan, MacIP, ShieldVlan


@admin.register(Vlan)
class VlanAdmin(admin.ModelAdmin):
    list_display_links = ('name',)
    list_display = ('id', 'br', 'vlan_id', 'name', 'tag', 'enable', 'group', 'subnet_ip', 'net_mask', 'gateway',
                    'subnet_ip_v6', 'net_mask_v6', 'gateway_v6', 'dns_server_v6', 'dns_server', 'dhcp_config_v6')
    list_filter = ('enable', 'tag')
    search_fields = ('name', 'br', 'vlan_id')
    list_select_related = ('group',)


@admin.register(MacIP)
class MacIPAdmin(admin.ModelAdmin):
    list_display_links = ('id', 'ipv4',)
    list_display = ('id', 'ip_vm', 'get_attach_ip', 'ipv4', 'ipv6', 'mac', 'vlan', 'enable', 'used', 'desc')
    list_filter = ('vlan', 'enable')
    search_fields = ('ipv4', 'ipv6')
    list_select_related = ('vlan',)

    def get_attach_ip(self, obj):
        if obj.attach_ip:
            return obj.attach_ip

    get_attach_ip.short_description = '附加IP虚拟机'


@admin.register(ShieldVlan)
class ShieldVlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_name', 'get_vlan_id')
    list_filter = ('user_name',)
    search_fields = ('user_name',)
    filter_horizontal = ('vlan_id',)

    def get_vlan_id(self, obj):
        return obj.get_vlan_id()

