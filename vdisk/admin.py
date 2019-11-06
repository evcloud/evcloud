from django.contrib import admin

from .models import Vdisk, Quota

# Register your models here.

@admin.register(Quota)
class QuotaAdmin(admin.ModelAdmin):
    list_display_links = ('id',)
    list_display = ( 'id', 'name', 'group', 'cephpool', 'total', 'size_used', 'max_vdisk')
    search_fields = ['name']
    list_filter = ['group', 'cephpool']


@admin.register(Vdisk)
class VdiskAdmin(admin.ModelAdmin):
    list_display_links = ('uuid',)
    list_display = ( 'uuid', 'size', 'quota', 'vm', 'dev', 'enable', 'user', 'create_time', 'attach_time', 'remarks')
    search_fields = ['uuid', 'vm','remarks']
    list_filter = ['quota', 'user']



