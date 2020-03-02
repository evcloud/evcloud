from django.urls import path, re_path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'device'

urlpatterns = [
    path('', login_required(views.PCIView.as_view()), name='pci-list'),
    # path('create', login_required(views.VmCreateView.as_view()), name='vm-create'),
    # re_path(r'^detail/(?P<vm_uuid>[0-9a-z-]{32,36})/$', login_required(views.VmDetailView.as_view()), name='vm-detail'),

]
