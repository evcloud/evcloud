from django.conf.urls import include, url
from .views_v2 import *
from rest_framework.documentation import include_docs_urls


urlpatterns = [
    url(r'^centers/$', center_list),

    url(r'^groups/$', group_list),
    url(r'^groups/(?P<group_id>\d+)/$', group_detail),

    url(r'^storage_pools/$', pool_list),
    url(r'^volumes/$', volume_list),
    url(r'^volumes/(?P<volume_id>[\w\-\d]+)/$', volume_detail), 
    url(r'^volumes/(?P<volume_id>[\w\-\d]+)/vm/$', volume_vm), 

    url(r'^hosts/$', host_list),
    url(r'^hosts/(?P<host_id>\d+)/$', host_detail),

    url(r'^images/$', image_list),
    url(r'^images/(?P<image_id>\d+)/$', image_detail),

    url(r'^vms/$', vm_list),
    url(r'^vms/(?P<vm_id>[\w\-\d]+)/$', vm_detail),
    url(r'^vms/(?P<vm_id>[\w\-\d]+)/status/$', vm_status),
    url(r'^vms/(?P<vm_id>[\w\-\d]+)/operations/$', vm_operations),
    url(r'^vms/(?P<vm_id>[\w\-\d]+)/vnc/$', vm_vnc),
    url(r'^vnc/(?P<vnc_id>[\w\-\d]+)/$', vnc_detail),

    url(r'^vlans/$', vlan_list),
    url(r'^vlans/(?P<vlan_id>\d+)/$', vlan_detail),

]

urlpatterns += [
    url(r'^docs/', include_docs_urls(title='EVcloud API Documents'))
]