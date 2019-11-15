from django.contrib import admin

from .models import Vdisk, Quota

# Register your models here.

@admin.register(Quota)
class QuotaAdmin(admin.ModelAdmin):
    list_display_links = ('id',)
    list_display = ( 'id', 'name', 'group', 'cephpool', 'total', 'size_used', 'max_vdisk', 'get_stats_used')
    search_fields = ['name']
    list_filter = ['group', 'cephpool']

    def get_stats_used(self, obj):
        s = obj.get_all_disk_size()
        if s >= 0:
            return s
        return 'get error'

    get_stats_used.short_description = '实时统计的已使用容量(GB)'


@admin.register(Vdisk)
class VdiskAdmin(admin.ModelAdmin):
    list_display_links = ('uuid',)
    list_display = ( 'uuid', 'size', 'quota', 'vm', 'dev', 'enable', 'user', 'create_time', 'attach_time', 'get_deleted', 'remarks')
    search_fields = ['uuid', 'vm','remarks']
    list_filter = ['quota', 'user']

    def delete_queryset(self, request, queryset):
        '''
        后台管理批量删除重写， 通过每个对象的delete()方法删除，同时会删除ceph rbd image
        '''
        for obj in queryset:
            if not obj.is_mounted():    # 硬盘已挂载，不删除
                obj.delete()

    def get_deleted(self, obj):
        if obj.deleted:
            return '已删除'
        return '使用中'

    get_deleted.short_description = '删除状态'

