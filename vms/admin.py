from django.contrib import admin

from .models import Vm
# Register your models here.

@admin.register(Vm)
class VmAdmin(admin.ModelAdmin):
    list_display_links = ('uuid', 'name',)
    list_display = ( 'uuid', 'name', 'mac_ip', 'vcpu', 'mem', 'host', 'user', 'create_time', 'remarks')
    search_fields = ['name','mac_ip__name']
    list_filter = ['host', 'user']

