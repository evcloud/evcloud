from django.conf.urls import include, url
from views import *

urlpatterns = [
    url(r'^auth/login/$',   auth_login),
    url(r'^auth/logout/$',  auth_logout),
               
    url(r'^center/get_list/$',  center_get_list),
    url(r'^group/get/$',   group_get),
    url(r'^group/get_list/$',   group_get_list),
    url(r'^ceph/get_list/$',    ceph_get_list),
    url(r'^host/get/$',    host_get),
    url(r'^host/get_list/$',    host_get_list),
    url(r'^image/get/$',        image_get),
    url(r'^image/get_list/$',   image_get_list),
    url(r'^vm/get/$',       vm_get),
    url(r'^vm/get_list/$',  vm_get_list),
    url(r'^vm/create/$',    vm_create),
    url(r'^vm/status/$',    vm_status),
    url(r'^vm/op/$',        vm_op),
    url(r'^vm/edit/$',      vm_edit),
    url(r'^vnc/open/$',     vnc_open),
    url(r'^vnc/close/$',    vnc_close),
    
    
    url(r'^net/vlan/get/$',    net_get_vlan),
    url(r'^net/vlan/get_list/$',    net_get_vlan_list),
]