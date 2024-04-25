from django.contrib import admin
from django.contrib import messages

from .models import Vm, VmArchive, VmLog, VmDiskSnap, MigrateTask, Flavor, AttachmentsIP, ErrorLog


@admin.register(Vm)
class VmAdmin(admin.ModelAdmin):
    admin_order = 1
    list_display_links = ('hex_uuid',)
    list_display = ('hex_uuid', 'mac_ip', 'image', 'vcpu', 'mem', 'host', 'sys_disk_size',
                    'disk_type', 'user', 'create_time', 'remarks',
                    'image_name', 'default_user', 'default_password', 'image_size', 'sys_type', 'version',
                    'release', 'architecture', 'boot_mode',  'ceph_pool', 'image_parent', 'image_snap')
    search_fields = ['name', 'mac_ip__ipv4']
    list_filter = ['host', 'user']
    raw_id_fields = ('mac_ip', 'host', 'user', 'image')

    actions = ['update_sys_disk_size', ]

    @admin.action(description="更新系统盘的大小")
    def update_sys_disk_size(self, request, queryset):
        ok_count = 0
        failed_count = 0
        err = None
        for obj in queryset:
            try:
                obj.update_sys_disk_size()
                ok_count += 1
            except Exception as e:
                err = e
                failed_count += 1

        if failed_count:
            self.message_user(request=request, message=f'更新系统盘的大小 {ok_count}成功 {failed_count}失败, {str(err)}',
                              level=messages.ERROR)
        else:
            self.message_user(request=request, message=f'更新系统盘的大小成功{ok_count}', level=messages.SUCCESS)


def clear_vm_sys_disk(modeladmin, request, queryset):
    exc = None
    failed_count = 0
    success_count = 0
    for obj in queryset:
        try:
            obj.rm_sys_disk_snap()
            try:
                obj.rm_sys_disk(raise_exception=True)
            except Exception as e:
                raise Exception(f'remove rbd image of disk error, {str(e)}')
            success_count = success_count + 1
        except Exception as e:
            failed_count = failed_count + 1
            exc = e
            continue

    if exc is not None:
        msg = f'归档虚拟机的系统镜像删除，{success_count}个成功，{failed_count}个失败，error: {exc}'
        modeladmin.message_user(request=request, message=msg, level=messages.ERROR)
    else:
        msg = f'成功删除{success_count}个归档虚拟机的系统镜像'
        modeladmin.message_user(request=request, message=msg, level=messages.SUCCESS)


def undefine_vm_from_host(modeladmin, request, queryset):
    exc = None
    failed_count = 0
    success_count = 0
    for obj in queryset:
        try:
            obj.check_and_release_host()
            success_count = success_count + 1
        except Exception as e:
            failed_count = failed_count + 1
            exc = e
            continue

    if exc is not None:
        msg = f'宿主机资源清理释放，{success_count}个成功，{failed_count}个失败，error: {exc}'
        modeladmin.message_user(request=request, message=msg, level=messages.ERROR)
    else:
        msg = f'成功清理释放{success_count}个归档虚拟机所占用的宿主机资源'
        modeladmin.message_user(request=request, message=msg, level=messages.SUCCESS)


def clear_vm_sys_snapshots(modeladmin, request, queryset):
    """清除系统快照（用户发布镜像时创建的保护快照）"""
    exc = None
    failed_count = 0
    success_count = 0
    for obj in queryset:
        try:
            obj.rm_sys_snapshots()
            success_count = success_count + 1
        except Exception as e:
            failed_count = failed_count + 1
            exc = e
            continue
            # raise Exception(f'remove rbd image protected snap error, {str(e)}')

    if exc is not None:
        msg = f'删除受保护的快照，{success_count}个成功，{failed_count}个失败，error: {exc}'
        modeladmin.message_user(request=request, message=msg, level=messages.ERROR)
    else:
        msg = f'成功删除{success_count}个镜像内的所有受保护的镜像'
        modeladmin.message_user(request=request, message=msg, level=messages.SUCCESS)


clear_vm_sys_disk.short_description = "清除所选的虚拟机的系统盘和快照"
undefine_vm_from_host.short_description = "释放所选虚拟机所占用宿主机的资源"
clear_vm_sys_snapshots.short_description = '清除所选的虚拟机镜像中的保护快照'


@admin.register(VmArchive)
class VmArchiveAdmin(admin.ModelAdmin):
    admin_order = 2
    list_display_links = ('id',)
    list_display = ('id', 'uuid', 'ipv4', 'vcpu', 'mem', 'mac', 'disk_type', 'disk', 'sys_disk_size', 'image_parent',
                    'center_name', 'group_name', 'host_ipv4', 'host_released', 'user', 'archive_time', 'remarks')
    search_fields = ['uuid', 'center_name', 'remarks', 'user']
    list_filter = ['host_released', 'center_name', 'group_name', 'host_ipv4', 'user']
    list_editable = ['host_released', ]
    actions = [clear_vm_sys_disk, undefine_vm_from_host, clear_vm_sys_snapshots]

    def delete_queryset(self, request, queryset):
        """
        后台管理批量删除重写， 通过每个对象的delete()方法删除，同时会删除ceph rbd image
        """
        exc = None
        failed_count = 0
        success_count = 0
        for obj in queryset:
            try:
                obj.delete()
                success_count = success_count + 1
            except Exception as e:
                failed_count = failed_count + 1
                exc = e
                continue

        if exc is not None:
            msg = f'删除归档虚拟机，{success_count}个成功，{failed_count}个失败，error: {exc}'
            self.message_user(request=request, message=msg, level=messages.ERROR)


@admin.register(VmLog)
class VmLogAdmin(admin.ModelAdmin):
    list_display_links = ('id', 'title',)
    list_display = ('id', 'title', 'about', 'create_time')
    search_fields = ['title', 'content']
    list_filter = ['about']


@admin.register(VmDiskSnap)
class VmDiskSnapAdmin(admin.ModelAdmin):
    admin_order = 3
    list_display_links = ('id',)
    list_display = ('id', 'snap', 'disk', 'vm', 'create_time', 'remarks')
    search_fields = ['disk', 'remarks']
    list_filter = ['vm']

    def delete_queryset(self, request, queryset):
        """
        后台管理批量删除重写， 通过每个对象的delete()方法删除，同时会删除ceph rbd image snap
        """
        for obj in queryset:
            obj.delete()


@admin.register(MigrateTask)
class MigrateTaskAdmin(admin.ModelAdmin):
    admin_order = 4
    list_display_links = ('id',)
    list_display = ('id', 'vm_uuid', 'src_host_ipv4', 'src_is_free', 'dst_host_ipv4', 'dst_is_claim', 'status', 'tag', 'src_undefined', 'migrate_time')
    search_fields = ('vm_uuid', 'content')
    list_filter = ('status', 'src_undefined', 'tag')


@admin.register(Flavor)
class FlavorAdmin(admin.ModelAdmin):
    admin_order = 5
    list_display_links = ('id',)
    list_display = ('id', 'vcpus', 'ram', 'public', 'enable')


@admin.register(AttachmentsIP)
class AttachmentsIPAdmin(admin.ModelAdmin):
    admin_order = 6
    list_display_links = ('id',)
    list_display = ('id', 'vm', 'sub_ip')


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    admin_order = 7
    list_display_links = ('id',)
    list_display = ('id', 'full_path', 'status_code', 'method', 'message', 'create_time', 'username')

