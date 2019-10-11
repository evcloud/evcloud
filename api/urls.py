from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView
from rest_framework.routers import DefaultRouter

from . import views

app_name = "api"

router = DefaultRouter()
router.register(r'(?P<version>(v3|v4))/vms', views.VmsViewSet, base_name='vms')


urlpatterns = [
    path(r'', include(router.urls)),
]
