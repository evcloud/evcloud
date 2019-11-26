from django.urls import path, re_path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'reports'

urlpatterns = [
    path('', login_required(views.ReportsListView.as_view()), name='reports-list'),
    # re_path(r'^detail/(?P<vm_uuid>[0-9a-z-]{32})/$', login_required(views.VmDetailView.as_view()), name='vm-detail'),
]
