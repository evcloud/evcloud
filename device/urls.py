from django.urls import path, re_path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'device'

urlpatterns = [
    path('', login_required(views.PCIView.as_view()), name='pci-list'),
    re_path(r'^mount/(?P<pci_id>[0-9]+)/$', login_required(views.PCIMountView.as_view()), name='pci-mount'),
]
