from django.contrib import admin, messages

from .models import VmXmlTemplate, Image, MirrorImageTask


@admin.register(VmXmlTemplate)
class VmXmlTemplateAdmin(admin.ModelAdmin):
    list_display_links = ('id', 'name',)
    list_display = ('id', 'name', 'desc', 'max_cpu_socket')
    search_fields = ('name', 'desc')


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display_links = ('id', 'name',)
    list_display = ('id', 'name', 'version', 'tag', 'sys_type', 'size', 'ceph_pool', 'base_image',
                    'snap', 'enable', 'xml_tpl', 'desc', 'mirror_image_market')
    search_fields = ('name',)
    list_filter = ('ceph_pool__ceph__center', 'sys_type', 'enable', 'tag')
    actions = ['update_image_size', ]

    @admin.action(description="更新镜像的大小")
    def update_image_size(self, request, queryset):
        ok_count = 0
        failed_count = 0
        err = None
        for obj in queryset:
            try:
                obj.update_size_from_ceph()
                ok_count += 1
            except Exception as e:
                err = e
                failed_count += 1

        if failed_count:
            self.message_user(request=request, message=f'更新镜像的大小 {ok_count}成功 {failed_count}失败, {str(err)}',
                              level=messages.ERROR)
        else:
            self.message_user(request=request, message=f'更新镜像的大小成功{ok_count}', level=messages.SUCCESS)

    # 重写编辑页, 继承父类方法
    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.fields = (
            'name', 'tag', 'sys_type', 'release', 'version', 'architecture', 'boot_mode', 'nvme_support', 'size',
            'ceph_pool', 'base_image',
            'snap', 'enable', 'xml_tpl', 'default_user', 'default_password', 'desc', 'user', 'create_time',
            'update_time', 'vm_host', 'vm_uuid', 'vm_mac_ip', 'vm_vcpu', 'vm_mem'
        )  # 将自定义的字段注册到编辑页中
        self.readonly_fields = (
            'snap', 'vm_host', 'vm_uuid', 'vm_mac_ip', 'vm_vcpu', 'vm_mem', 'create_time', 'update_time',)
        return super(ImageAdmin, self).change_view(request, object_id, form_url=form_url,
                                                   extra_context=extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        self.fields = (
            'name', 'tag', 'sys_type', 'release', 'version', 'architecture', 'boot_mode', 'nvme_support', 'size',
            'ceph_pool', 'base_image',
            'enable', 'xml_tpl', 'default_user', 'default_password', 'desc', 'user',
        )  # 将自定义的字段注册到新增页中
        return super(ImageAdmin, self).add_view(request, form_url=form_url, extra_context=extra_context)


@admin.register(MirrorImageTask)
class MirrorImageTaskAdmin(admin.ModelAdmin):
    list_display_links = ('id', 'mirror_image_name',)
    list_display = ('id', 'mirror_image_name', 'mirror_image_sys_type', 'mirror_image_version', 'mirror_image_release',
                    'mirror_image_architecture', 'mirror_image_boot_mode', 'mirror_image_base_image',
                    'mirror_image_enable', 'mirror_image_xml_tpl', 'user', 'create_time', 'update_time', 'desc',
                    'mirror_image_default_user', 'mirror_image_default_password', 'mirror_image_size', 'operate',
                    'mirrors_image_service_url', 'status', 'import_date', 'import_date_complate',
                    'export_date', 'export_date_complate', 'error_msg', 'bucket_name', 'file_path', 'token',
                    'download_or_upload_status', 'create_os_image', 'xml_tpl_search')
    search_fields = ('mirror_image_name',)
