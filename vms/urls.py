from django.urls import path, re_path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'vms'

urlpatterns = [
    path('', login_required(views.VmsView.as_view()), name='vms-list'),
    path('create', login_required(views.VmCreateView.as_view()), name='vm-create'),
    re_path(r'^detail/(?P<vm_uuid>[0-9a-z-]{32,36})/$', login_required(views.VmDetailView.as_view()), name='vm-detail'),
    re_path(r'^mount-disk/(?P<vm_uuid>[0-9a-z-]{32,36})/$', login_required(views.VmMountDiskView.as_view()),
            name='vm-mount-disk'),
    re_path(r'^edit/(?P<vm_uuid>[0-9a-z-]{32,36})/$', login_required(views.VmEditView.as_view()), name='vm-edit'),
    re_path(r'^reset/(?P<vm_uuid>[0-9a-z-]{32,36})/$', login_required(views.VmResetView.as_view()), name='vm-reset'),
    re_path(r'^migrate/(?P<vm_uuid>[0-9a-z-]{32,36})/$', login_required(views.VmMigrateView.as_view()),
            name='vm-migrate'),
    re_path(r'^live-migrate/(?P<vm_uuid>[0-9a-z-]{32,36})/$', login_required(views.VmLiveMigrateView.as_view()),
            name='vm-live-migrate'),
    re_path(r'^mount-pci/(?P<vm_uuid>[0-9a-z-]{32,36})/$', login_required(views.VmMountPCIView.as_view()),
            name='vm-mount-pci'),
    re_path(r'^disk/expand/(?P<vm_uuid>[0-9a-z-]{32,36})/$', login_required(views.VmSysDiskExpandView.as_view()),
            name='vm-sys-disk-expand'),
    path('shelve-list', login_required(views.VmShelveView.as_view()), name='shelve-list'),
    re_path(r'unshelve/(?P<vm_uuid>[0-9a-z-]{32,36})/$', login_required(views.VmUnShelveView.as_view()),
            name='unshelve'),
    re_path(r'attach-ip/(?P<vm_uuid>[0-9a-z-]{32,36})/$', login_required(views.VmAttachIPView.as_view()),
            name='vm-attach-ip'),
    re_path(r'detach-ip/(?P<vm_uuid>[0-9a-z-]{32,36})/$', login_required(views.VmDetachIPView.as_view()),
            name='vm-detach-ip')

]
