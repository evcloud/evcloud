from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'vpn'

urlpatterns = [
    path('list/', login_required(views.VPNView.as_view()), name='vpn-list'),
    path('add/', login_required(views.VPNAddView.as_view()), name='vpn-add'),
    path('change/<int:id>/', login_required(views.VPNChangeView.as_view()), name='vpn-change'),
    path('delete/<int:id>/', login_required(views.VPNDeleteView.as_view()), name='vpn-delete')
]
