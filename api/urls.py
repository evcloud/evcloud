from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter


from . import views

app_name = "api"

router = DefaultRouter()
router.register(r'(?P<version>(v3|v4))/vms', views.VmsViewSet, base_name='vms')
router.register(r'(?P<version>(v3|v4))/center', views.CenterViewSet, base_name='center')
router.register(r'(?P<version>(v3|v4))/group', views.GroupViewSet, base_name='group')
router.register(r'(?P<version>(v3|v4))/host', views.HostViewSet, base_name='host')
router.register(r'(?P<version>(v3|v4))/image', views.ImageViewSet, base_name='image')
router.register(r'(?P<version>(v3|v4))/vlan', views.VlanViewSet, base_name='vlan')
router.register(r'(?P<version>(v3|v4))/vdisk', views.VDiskViewSet, base_name='vdisk')
router.register(r'(?P<version>(v3|v4))/quota', views.QuotaViewSet, base_name='quota')
router.register(r'(?P<version>(v3|v4))/stat', views.StatCenterViewSet, base_name='stat')
router.register(r'(?P<version>(v3|v4))/pci', views.PCIDeviceViewSet, base_name='pci_device')

urlpatterns = [
    path(r'', include(router.urls)),
    re_path(r'(?P<version>(v3|v4))/token/', views.AuthTokenViewSet.as_view(), name='token'),
    re_path(r'(?P<version>(v3|v4))/jwt/', views.JWTObtainPairView.as_view(), name='jwt_token'),
    re_path(r'(?P<version>(v3|v4))/jwt-refresh/', views.JWTRefreshView.as_view(), name='jwt_refresh'),
    re_path(r'(?P<version>(v3|v4))/jwt-verify/', views.JWTVerifyView.as_view(), name='jwt_verify'),
]
