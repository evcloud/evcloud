from django.contrib import admin

from .models import Vm, VmArchive, VmLog
# Register your models here.

@admin.register(Vm)
class VmAdmin(admin.ModelAdmin):
    list_display_links = ('uuid',)
    list_display = ( 'uuid', 'mac_ip', 'image', 'vcpu', 'mem', 'host', 'user', 'create_time', 'remarks')
    search_fields = ['name','mac_ip__name']
    list_filter = ['host', 'user']


@admin.register(VmArchive)
class VmArchiveAdmin(admin.ModelAdmin):
    list_display_links = ('id',)
    list_display = ('id', 'uuid', 'ipv4', 'vcpu', 'mem', 'mac', 'disk', 'image_parent', 'center_name', 'group_name',
                     'host_ipv4', 'user', 'archive_time', 'remarks')
    search_fields = ['uuid', 'center_name', 'remarks', 'user']
    list_filter = ['center_name', 'group_name', 'host_ipv4', 'user']


@admin.register(VmLog)
class VmLogAdmin(admin.ModelAdmin):
    list_display_links = ('id', 'title',)
    list_display = ( 'id', 'title', 'about', 'create_time')
    search_fields = ['title', 'content']
    list_filter = ['about',]
