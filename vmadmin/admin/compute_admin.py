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
    list_filter = ['group__center__name', 'group','enable']
    ordering = ('group', 'ipv4')
    filter_horizontal = ('vlan',)
    readonly_fields = ('vcpu_allocated', 'mem_allocated', 'vm_created')
  
class VmAdmin(VMModelAdmin):
    list_display = ('host', 'name', 'image', 'vcpu', 'mem', 'creator')
    list_filter = ['host__group__center__name', 'host__group__name', 'creator',]
    readonly_fields = ('host', 'image_id', 'image_snap', 'image',
                       'uuid', 'name', 'vcpu', 'mem', 'disk', 'deleted',
                       'creator', 'create_time')
    search_fields = ('host__ipv4', 'name', 'image', 'image_snap', 'uuid', 'disk', 'creator')

class VmArchiveAdmin(VMModelAdmin):
    list_display = ('uuid', 'center_name', 'group_name', 'host_ipv4', 'mac', 'ipv4', 'ceph_host', 
        'ceph_pool', 'image_snap', 'name', 'vcpu', 'mem', 'disk',  'vlan', 'br', 'remarks', 'archive_time', 'create_time', )
    list_filter = ['creator', 'center_name', 'group_name', 'host_ipv4', 'ceph_host', 'ceph_pool',]
    ordering = ('-archive_time',)
    readonly_fields = ('center_id', 'center_name', 'group_id', 'group_name', 'host_id', 'host_ipv4', 
        'ceph_host', 'ceph_pool', 'image_id', 'image_snap', 'name', 'uuid', 'vcpu', 'mem', 'disk', 
        'mac', 'ipv4', 'vlan', 'br', 'remarks', 'archive_time', 'create_time', 'creator')

    search_fields = list_display
    list_display_links = ()
    
    def has_add_permission(self, request):
        return False
    
#     def has_change_permission(self, request, obj=None):
#         return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    actions_on_top = False
    actions_on_bottom = False
    actions_selection_counter = False