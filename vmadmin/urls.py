from django.conf.urls import include, url
from .vm_views import *
from .gpu_views import *

urlpatterns = [
#     url(r'^(?P<url>.+)', root),
    url(r'^$', index_view),
    url(r'^vm/$', index_view),
    url(r'^vm/list/$', vm_list_view),
    url(r'^vm/create/$', vm_create_view),
    url(r'^vm/edit/$', vm_edit_view),
    url(r'^vm/vnc/$', vm_vnc_view),
    url(r'^vm/migrate/$', vm_migrate_view),
    url(r'^vm/detail/$', vm_detail_view),
    url(r'^vm/status/$', vm_status_ajax),
    url(r'^vm/op/$', vm_op_ajax),
    url(r'^vm/edit_remarks/$', vm_edit_remarks_ajax),

    url(r'^gpu/list/$', gpu_list_view),
    url(r'^gpu/mount/$', gpu_mount_view),
    url(r'^gpu/umount/$', gpu_umount_ajax),
    url(r'^gpu/detail/$', gpu_detail_view),
    url(r'^gpu/edit_remarks/$', gpu_edit_remarks_ajax),
]
