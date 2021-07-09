from django.contrib import admin

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
    list_display = ('id', 'ipv4', 'group', 'real_cpu', 'vcpu_total', 'vcpu_allocated', 'vcpu_allocated_now',
                    'mem_total', 'mem_reserved', 'mem_allocated', 'mem_allocated_now', 'vm_created', 'vm_created_now', 'enable', 'desc')
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
