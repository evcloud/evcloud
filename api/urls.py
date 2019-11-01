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

urlpatterns = [
    path(r'', include(router.urls)),
    re_path(r'(?P<version>(v3|v4))/token', views.AuthTokenViewSet.as_view(), name='token'),
]
