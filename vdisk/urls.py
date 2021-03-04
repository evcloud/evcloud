from django.urls import path, re_path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'vdisk'

urlpatterns = [
    path('', login_required(views.VdiskView.as_view()), name='vdisk-list'),
    path('create', login_required(views.VdiskCreateView.as_view()), name='vdisk-create'),
    re_path(r'^mount/(?P<disk_uuid>[0-9a-z-]{32})/$', login_required(views.DiskMountToVmView.as_view()), name='vdisk-mount-to-vm')
]
