from django.urls import path, re_path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'vms'

urlpatterns = [
    path('', login_required(views.VmsView.as_view()), name='vms-list'),
    path('create', login_required(views.VmCreateView.as_view()), name='vm-create'),
    re_path(r'^detail/(?P<vm_uuid>[0-9a-z-]{32,36})/$', login_required(views.VmDetailView.as_view()), name='vm-detail'),
    re_path(r'^mount/(?P<vm_uuid>[0-9a-z-]{32,36})/$', login_required(views.VmMountDiskView.as_view()), name='vm-mount-disk'),
    re_path(r'^edit/(?P<vm_uuid>[0-9a-z-]{32,36})/$', login_required(views.VmEditView.as_view()), name='vm-edit'),
    re_path(r'^reset/(?P<vm_uuid>[0-9a-z-]{32,36})/$', login_required(views.VmResetView.as_view()), name='vm-reset'),
    re_path(r'^migrate/(?P<vm_uuid>[0-9a-z-]{32,36})/$', login_required(views.VmMigrateView.as_view()), name='vm-migrate')
]

