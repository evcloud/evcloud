from django.contrib import admin

from .models import VmXmlTemplate, Image, ImageType
# Register your models here.

@admin.register(VmXmlTemplate)
class VmXmlTemplateAdmin(admin.ModelAdmin):
    list_display_links = ('id', 'name',)
    list_display = ( 'id', 'name', 'desc')
    search_fields = ['name', 'desc']


@admin.register(ImageType)
class ImageTypeAdmin(admin.ModelAdmin):
    list_display_links = ('id', 'name',)
    list_display = ( 'id', 'name')
    search_fields = ['name',]


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display_links = ('id', 'name',)
    list_display = ( 'id', 'name', 'version', 'tag', 'sys_type', 'type', 'base_image', 'snap', 'enable', 'xml_tpl', 'desc')
    search_fields = ['name',]
    list_filter = ['type', 'enable', 'tag', 'sys_type']


