#codign=utf-8
from .base import VMModelAdmin
from monitoring.models import *


class HostErrorLogAdmin(VMModelAdmin):	
    list_display_links = ('host_ipv4',)
    list_display = ('host_ipv4', 'host_id', 'info', 'create_time', 'deleted')
    list_filter = ['host_ipv4']
    readonly_fields = ['host_id','host_ipv4','create_time']


class VmMigrateLogAdmin(VMModelAdmin):
    list_display_links = ('vm_uuid',)
    list_display = ('host_error_log_id','vm_uuid','vm_ipv4','src_host_ipv4','dst_host_ipv4','migrate_res','create_time','deleted')
    list_filter = ['host_error_log_id', 'vm_uuid','vm_ipv4']
    readonly_fields = ['vm_uuid','vm_ipv4','src_host_ipv4','dst_host_ipv4','migrate_res','create_time',]
