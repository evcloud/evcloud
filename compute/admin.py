from django.contrib import admin
from django.db.models import Q
from pcservers.models import PcServer
from .models import Center, Group, Host


@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    list_display_links = ('name',)
    list_display = ('id', 'name', 'location', 'desc', 'ceph_clusters_list')
    list_filter = ['location']
    search_fields = ['name', 'location']

    # 显示多对多字段, 定义一个方法，遍历，然后用列表返回
    # Field producer_country
    def ceph_clusters_list(self, obj):
        return [str(item) for item in obj.ceph_clusters.all()]
    ceph_clusters_list.short_description = 'CEPH集群'  # admin后台此字段表列显示名称，等价于模型字段verbose_name参数


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
    list_display = ('id', 'ipv4', 'group', 'real_cpu', 'real_mem', 'vcpu_total', 'vcpu_allocated', 'vcpu_allocated_now',
                    'mem_total', 'mem_allocated', 'mem_allocated_now', 'vm_created', 'vm_created_now', 'enable', 'desc')
    list_filter = ['group']
    search_fields = ['ipv4']

    def vcpu_allocated_now(self, obj):
        s = obj.stats_vcpu_mem_vms_now()
        return s.get('vcpu')

    vcpu_allocated_now.short_description = '实时统计的已分配VCPU'

    def mem_allocated_now(self, obj):
        s = obj.stats_vcpu_mem_vms_now()
        return s.get('mem')

    mem_allocated_now.short_description = '实时统计的已分配MEM'

    def vm_created_now(self, obj):
        s = obj.stats_vcpu_mem_vms_now()
        return s.get('vm_num')

    vm_created_now.short_description = '实时统计虚拟机数'



    def group(self,obj):
        return obj.desc.group
    group.short_description = "group"

    # 重写编辑页, 继承父类方法
    def change_view(self, request, object_id, extra_context=None):
        self.fields = ('id',  'pcserver','group', 'ipv4','real_cpu', 'real_mem', 'vcpu_total', 'vcpu_allocated',
                    'mem_total', 'mem_allocated','vm_limit','vm_created', 'enable', 'desc')  # 将自定义的字段注册到编辑页中
        self.readonly_fields = ('id','ipv4')
        return super(HostAdmin, self).change_view(request, object_id, extra_context=extra_context)

    def add_view(self, request, extra_context=None):
        self.fields = ('group','pcserver', 'ipv4','real_cpu', 'real_mem', 'vcpu_total', 'vcpu_allocated',
                    'mem_total','vm_limit','mem_allocated','vm_created', 'enable', 'desc','ipmi_host','ipmi_user','ipmi_password')  # 将自定义的字段注册到编辑页中
        self.readonly_fields = ('ipv4',)
        return super(HostAdmin, self).add_view(request, extra_context=extra_context)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if '/add/' in request.path:
            if db_field.name == "pcserver":
                kwargs["queryset"] = PcServer.objects.filter(pc_server_host__isnull= True)
        elif '/change/' in request.path:
            if db_field.name == "pcserver":
                object_id = int(request.resolver_match.kwargs.get('object_id'))
                kwargs["queryset"] = PcServer.objects.filter(Q(pc_server_host__isnull = True) | Q(pc_server_host__id = object_id))
        return super(HostAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


    class Media:
        js = ('compute/custom.js',
              'jquery/jquery-3.4.1.min.js',
             )


