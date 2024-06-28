from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter

from .views import views, compute_view
from .views.logrecord_view import LogRecordViewSet
from .views.mirror_image_task_view import MirrorImageTaskViewSet

app_name = "api"

router = DefaultRouter()
router.register(r'vms', views.VmsViewSet, basename='vms')
router.register(r'center', views.CenterViewSet, basename='center')
router.register(r'group', views.GroupViewSet, basename='group')
router.register(r'host', views.HostViewSet, basename='host')
router.register(r'image', views.ImageViewSet, basename='image')
router.register(r'vlan', views.VlanViewSet, basename='vlan')
router.register(r'vdisk', views.VDiskViewSet, basename='vdisk')
router.register(r'quota', views.QuotaViewSet, basename='quota')
router.register(r'stat', views.StatCenterViewSet, basename='stat')
router.register(r'pci', views.PCIDeviceViewSet, basename='pci-device')
router.register(r'macip', views.MacIPViewSet, basename='macip')
router.register(r'flavor', views.FlavorViewSet, basename='flavor')
router.register(r'vpn', views.VPNViewSet, basename='vpn')
router.register(r'task/vm-migrate', views.MigrateTaskViewSet, basename='vm-migrate-task')
router.register(r'version', views.VersionViewSet, basename='version')
router.register(r'logrecord', LogRecordViewSet, basename='log-record')
router.register(r'mirror', MirrorImageTaskViewSet, basename='mirror-image')


no_router = DefaultRouter(trailing_slash=False)
no_router.register(r'compute/quota', compute_view.ComputeQuotaViewSet, basename='compute-quota')


urlpatterns = [
    path('', include(router.urls)),
    path('', include(no_router.urls)),
    re_path(r'token/', views.AuthTokenViewSet.as_view(), name='token'),
    re_path(r'jwt/', views.JWTObtainPairView.as_view(), name='jwt-token'),
    re_path(r'jwt-refresh/', views.JWTRefreshView.as_view(), name='jwt-refresh'),
    re_path(r'jwt-verify/', views.JWTVerifyView.as_view(), name='jwt-verify'),
]
