from django.urls import path, include
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'vpn'

urlpatterns = [
    # path('', login_required(views.VPNView.as_view()), name='vpn'),
]
