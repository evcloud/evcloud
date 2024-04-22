from django.urls import path, re_path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'reports'

urlpatterns = [
    path('', login_required(views.ReportsListView.as_view()), name='reports-list'),
    path('host/<str:host_ipv4>', login_required(views.ReportHostCpuMem.as_view()), name='reports-info'),
    path('host/detect/', login_required(views.ReportsHostBatchDetection.as_view()), name='reports-detect'),
    path('host/batchsave/', login_required(views.ReportsHostBatchSave.as_view()), name='reports-batch-save'),
    re_path(r'^center/(?P<id>[0-9]+)/$', login_required(views.ReportsCenterView.as_view()), name='reports-center'),
    re_path(r'^group/(?P<id>[0-9]+)/$', login_required(views.ReportsGroupView.as_view()), name='reports-group'),
    path('quota', login_required(views.QuotaView.as_view()), name='reports-quota'),
]
