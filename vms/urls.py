from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'vms'

urlpatterns = [
    path('', login_required(views.VmsView.as_view()), name='vms-list'),
    path('create', login_required(views.VmCreateView.as_view()), name='vm-create')
]

