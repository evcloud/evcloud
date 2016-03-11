#codign=utf-8
from .base import VMModelAdmin
from image.models import *
 
class CephHostAdmin(VMModelAdmin):
    list_display = ('center', 'host', 'port', 'uuid')
    ordering = ('host',)
 
class CephPoolAdmin(VMModelAdmin):
    list_display = ('host', 'pool', 'type', 'enable', 'remarks')
    ordering = ('host', 'pool')