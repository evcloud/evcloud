from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "api"

router = DefaultRouter()
router.register(r'vms', views.VmsViewSet, base_name='vms')
router.register(r'center', views.CenterViewSet, base_name='center')
router.register(r'group', views.GroupViewSet, base_name='group')
router.register(r'host', views.HostViewSet, base_name='host')
router.register(r'image', views.ImageViewSet, base_name='image')
router.register(r'vlan', views.VlanViewSet, base_name='vlan')
router.register(r'vdisk', views.VDiskViewSet, base_name='vdisk')
router.register(r'quota', views.QuotaViewSet, base_name='quota')
router.register(r'stat', views.StatCenterViewSet, base_name='stat')
router.register(r'pci', views.PCIDeviceViewSet, base_name='pci-device')
router.register(r'macip', views.MacIPViewSet, base_name='macip')

urlpatterns = [
    path('', include(router.urls)),
    re_path(r'token/', views.AuthTokenViewSet.as_view(), name='token'),
    re_path(r'jwt/', views.JWTObtainPairView.as_view(), name='jwt-token'),
    re_path(r'jwt-refresh/', views.JWTRefreshView.as_view(), name='jwt-refresh'),
    re_path(r'jwt-verify/', views.JWTVerifyView.as_view(), name='jwt-verify'),
]
