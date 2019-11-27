from django.urls import path, re_path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'reports'

urlpatterns = [
    path('', login_required(views.ReportsListView.as_view()), name='reports-list'),
    re_path(r'^center/(?P<id>[0-9]+)/$', login_required(views.ReportsCenterView.as_view()), name='reports-center'),
    re_path(r'^group/(?P<id>[0-9]+)/$', login_required(views.ReportsGroupView.as_view()), name='reports-group'),
]
