from django.contrib import admin
from .models import PCIDevice

# Register your models here.

@admin.register(PCIDevice)
class PCIDeviceAdmin(admin.ModelAdmin):
    list_display_links = ('id',)
    list_display = ( 'id', 'type', 'host', 'address', 'vm', 'attach_time', 'enable', 'remarks')
    search_fields = ('remarks',)
    list_filter = ('type',)

