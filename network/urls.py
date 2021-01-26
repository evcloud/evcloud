from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'network'

urlpatterns = [
    path('vlan_list/', login_required(views.vlan_list), name='vlan_list'),
    path('vlan_add/', login_required(views.vlan_add), name='vlan_add'),
    path('vlan_show/', login_required(views.vlan_show), name='vlan_show'),
    ]
