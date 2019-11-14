from django.urls import path, include

from . import views

app_name = 'network'

urlpatterns = [
    path('vlan_list/', views.vlan_list, name='vlan_list'),
    path('vlan_add/', views.vlan_add, name='vlan_add'),
    path('vlan_show/', views.vlan_show, name='vlan_show'),
    ]
