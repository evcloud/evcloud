#codign=utf-8
from .base import VMModelAdmin
from image.models import *

class ImageTypeAdmin(VMModelAdmin):
    list_display = ('name', 'order')
    ordering = ('order',)

class ImageAdmin(VMModelAdmin):
    list_display_links = ('name',)
    list_display = ('cephpool', 'name', 'version', 'snap', 'desc', 'xml', 'enable', 'type', 'order')
    list_filter = ['cephpool', 'name', 'enable', 'type']
    search_fields = ['version', 'snap', 'desc']
    ordering = ('order',)
 
class XmlAdmin(VMModelAdmin):
    list_display_links = ('name',)
    list_display = ('name', 'desc')
    # ordering = ('ceph', 'name', 'version')