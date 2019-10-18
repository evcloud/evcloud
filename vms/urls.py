from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'vms'

urlpatterns = [
    path('', login_required(views.VmsView.as_view()), name='vms'),
]

