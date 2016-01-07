#codign=utf-8
from .base import VMModelAdmin
from image.models import *

class VlanTypeAdmin(VMModelAdmin):
    list_display = ('code', 'name')

class VlanAdmin(VMModelAdmin):
    list_display = ('vlan', 'br', 'type', 'enable', 'remarks')
    # list_filter = ['host', 'image',]
 
 
class MacIPAdmin(VMModelAdmin):
    list_display = ('vlan', 'mac', 'ipv4', 'vmid', 'enable')
    list_filter = ['vlan', 'enable',]
    readonly_fields = ('vmid',)