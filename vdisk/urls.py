from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'vdisk'

urlpatterns = [
    path('', login_required(views.VdiskView.as_view()), name='vdisk-list'),
    # path('create', login_required(views.VmCreateView.as_view()), name='vm-create')
]