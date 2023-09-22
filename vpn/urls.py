from django.urls import path, include
from django.contrib.auth.decorators import login_required
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'vpn'

router2 = DefaultRouter(trailing_slash=False)
router2.register(r'vpnfile', views.VPNFileViewSet, basename='vpn-file')

urlpatterns = [
    path('list/', login_required(views.VPNView.as_view()), name='vpn-list'),
    path('add/', login_required(views.VPNAddView.as_view()), name='vpn-add'),
    path('change/<int:id>/', login_required(views.VPNChangeView.as_view()), name='vpn-change'),
    path('delete/<int:id>/', login_required(views.VPNDeleteView.as_view()), name='vpn-delete'),
    path('vpnloginlog/', login_required(views.VPNLoginLog.as_view()), name='vpn-login-log'),
    path('', include(router2.urls)),
]
