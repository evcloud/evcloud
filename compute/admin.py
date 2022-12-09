from django.contrib import admin
from django.db.models import Sum, Subquery, Count, Q
from django.contrib import messages

from pcservers.models import PcServer
from image.models import Image
from .models import Center, Group, Host
from utils.ev_libvirt.virt import VirtHost, VirHostDown


@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    list_display_links = ('name',)
    list_display = ('id', 'name', 'location', 'desc', 'ceph_clusters_list')
    list_filter = ['location']
    search_fields = ['name', 'location']

    # 显示多对多字段, 定义一个方法，遍历，然后用列表返回
    # Field producer_country
    @admin.display(description='CEPH集群')
    def ceph_clusters_list(self, obj):
        return [str(item) for item in obj.ceph_clusters.all()]


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display_links = ('name',)
    list_display = ('id', 'name', 'center', 'desc')
    list_filter = ['center']
    search_fields = ['name']
    filter_horizontal = ['users']


@admin.register(Host)
class HostAdmin(admin.ModelAdmin):
    list_display_links = ('ipv4',)
    list_display = ('id', 'ipv4', 'group', 'pc_server_resource', 'vcpu_total', 'vcpu_allocated',
                    'mem_total', 'mem_allocated', 'vm_limit', 'vm_created', 'enable', 'desc')
    list_filter = ['group']
    search_fields = ['ipv4']
    actions = ['test_connect_host', 'update_host_quota']

    @admin.display(description='测试宿主机是否可访问连接')
    def test_connect_host(self, request, queryset):
        """
        测试宿主机是否可访问连接
        """
        down_hosts = []
        not_conn_hosts = []
        for host in queryset:
            vh = VirtHost(host_ipv4=host.ipv4)
            try:
                vh.get_connection()
            except VirHostDown:
                down_hosts.append(host.ipv4)
            except vh.VirtError:
                not_conn_hosts.append(host.ipv4)
            finally:
                vh.close()

        if down_hosts or not_conn_hosts:
            if down_hosts:
                self.message_user(request, f"无法访问宿主机{len(down_hosts)}个: {down_hosts}", level=messages.ERROR)
            if not_conn_hosts:
                self.message_user(request, f"无法连接宿主机{len(not_conn_hosts)}个: {not_conn_hosts}", level=messages.ERROR)
        else:
            self.message_user(request, "所选宿主机都可访问连接", level=messages.SUCCESS)

    @admin.display(description='更新宿主机的资源使用量')
    def update_host_quota(self, request, queryset):
        """
        更新宿主机的资源使用量
        """
        failed_hosts = []
        for host in queryset:
            try:
                if host.ipv4 == '127.0.0.1':
                    s = Image.objects.filter(vm_uuid__isnull=False).aggregate(vcpu_now=Sum('vm_vcpu'),
                                                                              mem_now=Sum('vm_mem'),
                                                                              count=Count('pk'))
                    vcpu_allocated = s.get('vcpu_now')
                    mem_allocated = s.get('mem_now')
                    vm_num = s.get('count')
                else:
                    s = host.stats_vcpu_mem_vms_now()
                    vcpu_allocated = s.get('vcpu')
                    mem_allocated = s.get('mem')
                    vm_num = s.get('vm_num')
                host.vcpu_allocated = vcpu_allocated
                host.mem_allocated = mem_allocated
                host.vm_created = vm_num
                host.save(update_fields=['vcpu_allocated', 'mem_allocated', 'vm_created'])
            except Exception:
                failed_hosts.append(host.ipv4)

        if failed_hosts:
            self.message_user(request, f"更新宿主机失败{len(failed_hosts)}个: {failed_hosts}", level=messages.ERROR)
        else:
            self.message_user(request, "所选宿主机都更新成功", level=messages.SUCCESS)

    @admin.display(description='真实物理资源')
    def pc_server_resource(self, obj):
        resource = f'{obj.pcserver.real_cpu}核/{obj.pcserver.real_mem}GB'
        return resource

    pc_server_resource.short_description = '真实物理资源'


    def group(self, obj):
        return obj.desc.group

    group.short_description = "group"

    # 重写编辑页, 继承父类方法
    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.fields = (
            'id', 'pcserver', 'group', 'ipv4', 'pc_server_resource', 'vcpu_total', 'vcpu_allocated',
            'mem_total', 'mem_allocated', 'vm_limit', 'vm_created', 'enable', 'desc'
        )  # 将自定义的字段注册到编辑页中
        self.readonly_fields = ('id', 'ipv4', 'pc_server_resource')
        return super(HostAdmin, self).change_view(request, object_id, form_url=form_url, extra_context=extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        self.fields = (
            'group', 'pcserver', 'ipv4', 'pc_server_resource', 'vcpu_total', 'vcpu_allocated',
            'mem_total', 'vm_limit', 'mem_allocated', 'vm_created', 'enable', 'desc', 'ipmi_host',
            'ipmi_user', 'ipmi_password'
        )  # 将自定义的字段注册到编辑页中
        self.readonly_fields = ('ipv4', 'pc_server_resource')
        return super(HostAdmin, self).add_view(request, form_url=form_url, extra_context=extra_context)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if '/add/' in request.path:
            if db_field.name == "pcserver":
                kwargs["queryset"] = PcServer.objects.filter(pc_server_host__isnull=True)
        elif '/change/' in request.path:
            if db_field.name == "pcserver":
                object_id = int(request.resolver_match.kwargs.get('object_id'))
                kwargs["queryset"] = PcServer.objects.filter(
                    Q(pc_server_host__isnull=True) | Q(pc_server_host__id=object_id))
        return super(HostAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    class Media:
        js = (
            'compute/custom.js',
            'jquery/jquery-3.4.1.min.js',
        )
