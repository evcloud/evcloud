#codign=utf-8
from .base import VMModelAdmin
from device.models import *

class DBGPUAdmin(VMModelAdmin):
    list_display_links = ('address',)
    list_display = ('host', 'address', 'vm', 'attach_time', 'enable', 'remarks')
    list_filter = ['host', 'enable']
    readonly_fields = ['vm', 'attach_time']
