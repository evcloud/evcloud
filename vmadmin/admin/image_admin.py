#codign=utf-8
from .base import VMModelAdmin
from image.models import *

class ImageTypeAdmin(VMModelAdmin):
    list_display = ('code', 'name', 'up_type')

class ImageAdmin(VMModelAdmin):
    list_display_links = ('name',)
    list_display = ('cephpool', 'name', 'version', 'snap', 'desc', 'xml', 'enable', 'type')
    list_filter = ['cephpool', 'name', 'enable', 'type']
    search_fields = ['version', 'snap', 'desc']
    ordering = ('cephpool', 'name', 'version')
 
class XmlAdmin(VMModelAdmin):
    list_display_links = ('name',)
    list_display = ('name', 'desc')
    # ordering = ('ceph', 'name', 'version')