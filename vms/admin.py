from django.contrib import admin

from .models import Vm, VmArchive, VmLog, VmDiskSnap, MigrateLog
# Register your models here.


@admin.register(Vm)
class VmAdmin(admin.ModelAdmin):
    list_display_links = ('hex_uuid',)
    list_display = ('hex_uuid', 'mac_ip', 'image', 'vcpu', 'mem', 'host', 'user', 'create_time', 'remarks')
    search_fields = ['name', 'mac_ip__name']
    list_filter = ['host', 'user']
    raw_id_fields = ('mac_ip', 'host', 'user', 'image')


@admin.register(VmArchive)
class VmArchiveAdmin(admin.ModelAdmin):
    list_display_links = ('id',)
    list_display = ('id', 'uuid', 'ipv4', 'vcpu', 'mem', 'mac', 'disk', 'image_parent', 'center_name', 'group_name',
                     'host_ipv4', 'user', 'archive_time', 'remarks')
    search_fields = ['uuid', 'center_name', 'remarks', 'user']
    list_filter = ['center_name', 'group_name', 'host_ipv4', 'user']

    def delete_queryset(self, request, queryset):
        '''
        后台管理批量删除重写， 通过每个对象的delete()方法删除，同时会删除ceph rbd image
        '''
        for obj in queryset:
            obj.delete()


@admin.register(VmLog)
class VmLogAdmin(admin.ModelAdmin):
    list_display_links = ('id', 'title',)
    list_display = ( 'id', 'title', 'about', 'create_time')
    search_fields = ['title', 'content']
    list_filter = ['about',]


@admin.register(VmDiskSnap)
class VmDiskSnapAdmin(admin.ModelAdmin):
    list_display_links = ('id',)
    list_display = ( 'id', 'snap', 'disk', 'vm', 'create_time', 'remarks')
    search_fields = ['disk', 'remarks']
    list_filter = ['vm',]

    def delete_queryset(self, request, queryset):
        '''
        后台管理批量删除重写， 通过每个对象的delete()方法删除，同时会删除ceph rbd image snap
        '''
        for obj in queryset:
            obj.delete()


@admin.register(MigrateLog)
class MigrateLogAdmin(admin.ModelAdmin):
    list_display_links = ('id',)
    list_display = ('id', 'vm_uuid', 'src_host_ipv4', 'dst_host_ipv4', 'result', 'src_undefined', 'migrate_time')
    search_fields = ('vm_uuid', 'content')
    list_filter = ('result', 'src_undefined')
