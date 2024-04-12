from django.contrib import admin
from django.forms import ModelForm

from .models import Vlan, MacIP, ShieldVlan
from django.core.exceptions import ValidationError


@admin.register(Vlan)
class VlanAdmin(admin.ModelAdmin):
    list_display_links = ('name',)
    list_display = ('id', 'br', 'vlan_id', 'name', 'tag', 'enable', 'image_specialized', 'group', 'subnet_ip', 'net_mask', 'gateway',
                    'subnet_ip_v6', 'net_mask_v6', 'gateway_v6', 'dns_server_v6', 'dns_server', 'dhcp_config_v6')
    list_filter = ('enable', 'tag')
    search_fields = ('name', 'br', 'vlan_id')
    list_select_related = ('group',)


@admin.register(MacIP)
class MacIPAdmin(admin.ModelAdmin):
    list_display_links = ('id', 'ipv4',)
    list_display = ('id', 'ipv4', 'enable', 'used', 'mac', 'ip_vm', 'get_attach_ip', 'ipv6', 'vlan',  'desc')
    list_filter = ('vlan', 'enable')
    search_fields = ('ipv4', 'ipv6')
    list_select_related = ('vlan',)

    def get_attach_ip(self, obj):
        if obj.attach_ip:
            return obj.attach_ip

    get_attach_ip.short_description = '附加IP虚拟机'


class ShieldVlanForm(ModelForm):

    def clean(self):
        cleaned_data = super().clean()
        field1 = cleaned_data.get('user_name')
        obj = ShieldVlan.objects.filter(user_name=field1).all()
        if len(obj) == 1 and not self.instance.id:  # 添加数据 id 为 None
            self.add_error('user_name', ValidationError('该账户数据已存在，不能重复添加数据，只能修改。'))

        elif len(obj) > 1:
            self.add_error('user_name', ValidationError('该账户数据已存在多条数据，请删除其余数据，只保留一条数据。'))


@admin.register(ShieldVlan)
class ShieldVlanAdmin(admin.ModelAdmin):
    form = ShieldVlanForm
    list_display = ('id', 'user_name', 'get_vlan_id')
    list_filter = ('user_name',)
    search_fields = ('user_name',)
    filter_horizontal = ('vlan_id',)

    def get_vlan_id(self, obj):
        return obj.get_vlan_id()

