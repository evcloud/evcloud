from django.contrib import admin

from .models import Vm, VmArchive, VmLog, VmDiskSnap, MigrateLog, Flavor


@admin.register(Vm)
class VmAdmin(admin.ModelAdmin):
    list_display_links = ('hex_uuid',)
    list_display = ('hex_uuid', 'mac_ip', 'image', 'vcpu', 'mem', 'host', 'user', 'create_time', 'remarks')
    search_fields = ['name', 'mac_ip__ipv4']
    list_filter = ['host', 'user']
    raw_id_fields = ('mac_ip', 'host', 'user', 'image')


def clear_vm_sys_disk(modeladmin, request, queryset):
    exc = None
    for obj in queryset:
        try:
            obj.rm_sys_disk_snap()
            try:
                obj.rm_sys_disk(raise_exception=True)
            except Exception as e:
                raise Exception(f'remove rbd image of disk error, {str(e)}')
        except Exception as e:
            exc = e
            continue

    if exc is not None:
        raise exc


def undefine_vm_from_host(modeladmin, request, queryset):
    exc = None
    for obj in queryset:
        try:
            obj.check_and_release_host()
        except Exception as e:
            exc = e
            continue

    if exc is not None:
        raise exc


clear_vm_sys_disk.short_description = "清除所选的虚拟机的系统盘和快照"
undefine_vm_from_host.short_description = "释放所选虚拟机所在宿主机的资源"


@admin.register(VmArchive)
class VmArchiveAdmin(admin.ModelAdmin):
    list_display_links = ('id',)
    list_display = ('id', 'uuid', 'ipv4', 'vcpu', 'mem', 'mac', 'disk', 'image_parent', 'center_name', 'group_name',
                    'host_ipv4', 'host_released', 'user', 'archive_time', 'remarks')
    search_fields = ['uuid', 'center_name', 'remarks', 'user']
    list_filter = ['host_released', 'center_name', 'group_name', 'host_ipv4', 'user']
    actions = [clear_vm_sys_disk, undefine_vm_from_host]

    def delete_queryset(self, request, queryset):
        """
        后台管理批量删除重写， 通过每个对象的delete()方法删除，同时会删除ceph rbd image
        """
        exc = None
        for obj in queryset:
            try:
                obj.delete()
            except Exception as e:
                exc = e
                continue

        if exc is not None:
            raise exc


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


@admin.register(Flavor)
class FlavorAdmin(admin.ModelAdmin):
    list_display_links = ('id',)
    list_display = ('id', 'vcpus', 'ram', 'public', 'enable')
