from django.conf.urls import include, url
from .vm_views import *
from .gpu_views import *
from .volume_views import *
from .net_views import *
from .monitoring_views import *

urlpatterns = [
#     url(r'^(?P<url>.+)', root),
    url(r'^$', index_view),
    url(r'^vm/$', index_view),
    url(r'^vm/list/$', vm_list_view, name="vm_list"),
    url(r'^vm/create/$', vm_create_view),
    url(r'^vm/edit/$', vm_edit_view),
    url(r'^vm/vnc/$', vm_vnc_view),
    url(r'^vm/migrate/$', vm_migrate_view),
    url(r'^vm/reset/$', vm_reset_view),
    url(r'^vm/detail/$', vm_detail_view),
    url(r'^vm/status/$', vm_status_ajax),
    url(r'^vm/op/$', vm_op_ajax),
    url(r'^vm/batch_op/$', vm_batch_op_ajax),
    url(r'^vm/edit_remarks/$', vm_edit_remarks_ajax),

    # url(r'^vm/snap/list/$', vm_snap_list_view),
    url(r'^vm/snap/create/$', vm_snap_create_view),
    url(r'^vm/snap/rollback_ajax/$', vm_snap_rollback_ajax_view),
    url(r'^vm/snap/edit_remarks/$', vm_snap_edit_remarks_ajax),

    url(r'^gpu/list/$', gpu_list_view),
    url(r'^gpu/mount/$', gpu_mount_view),
    url(r'^gpu/umount/$', gpu_umount_ajax),
    # url(r'^gpu/detail/$', gpu_detail_view),
    url(r'^gpu/edit_remarks/$', gpu_edit_remarks_ajax),

    url(r'^volume/list/$', volume_list_view),
    url(r'^volume/create/$', volume_create_view),
    url(r'^volume/mount/$', volume_mount_ceph_view),
    url(r'^volume/mount_ajax/$', volume_mount_ceph_ajax),
    url(r'^volume/delete/$', volume_delete_ajax),
    url(r'^volume/edit_remarks/$', volume_edit_remarks_ajax),
    url(r'^volume/umount/$', volume_umount_ceph_ajax),
    url(r'^volume/vm/create/$', volume_vm_create_view),
    url(r'^volume/cephpool_list/$', volume_cephpool_list_ajax),

    url(r'^net/vlan/list/$', net_vlan_list_view),
    url(r'^net/vlan/edit_remarks/$', net_vlan_edit_remarks_ajax),
    url(r'^net/vlan/ip/list/$', net_vlan_ip_list_view),
    url(r'^net/vlan/ip/batch_create/$', net_batch_create_macip),
    url(r'^net/vlan/ip/conf_file/$', net_vlan_conf_file_view),

    url(r'^monitoring/host_error/list/$', host_err_log_list_view),
    
]
