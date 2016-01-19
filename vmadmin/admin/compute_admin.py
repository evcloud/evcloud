#codign=utf-8
from .base import VMModelAdmin
from compute.models import *

class CenterAdmin(VMModelAdmin):
    list_display = ('name','location','desc','order')
    ordering = ('order',)
  
class GroupAdmin(VMModelAdmin):
    list_display_links = ('name',)
    list_display = ('name','center','desc','order')
    list_filter = ['center']
    filter_horizontal = ('admin_user',)
    ordering = ('order',)
 
class HostAdmin(VMModelAdmin):
    list_display_links = ('ipv4',)
    list_display = ('ipv4','group', 'vcpu_total','vcpu_allocated','mem_total', 'mem_allocated',
        'vm_limit', 'vm_created', 'enable', 'desc')
    list_filter = ['group','enable']
    ordering = ('group', 'ipv4')
    filter_horizontal = ('vlan',)
    readonly_fields = ('vcpu_allocated', 'mem_allocated', 'vm_created')
  
class VmAdmin(VMModelAdmin):
    list_display = ('host', 'name', 'image', 'vcpu', 'mem', 'creator')
    list_filter = ['host', 'image',]
    readonly_fields = ('host', 'image_id', 'image_snap', 'image',
                       'uuid', 'name', 'vcpu', 'mem', 'disk', 'deleted',
                       'creator', 'create_time')