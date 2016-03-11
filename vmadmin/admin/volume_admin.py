#codign=utf-8
from .base import VMModelAdmin
from django import forms 
from compute.models import Group

class CephVolumeAdmin(VMModelAdmin):
    list_display = ('uuid', 'user', 'group', 'cephpool', 'creator', 'create_time', 'size',
        'remarks', 'vm', 'attach_time', 'dev', 'enable')
    ordering = ('create_time',)
 
class CephQuotaAdmin(VMModelAdmin):
    list_display = ('group','total','volume')
    ordering = ('group',)
