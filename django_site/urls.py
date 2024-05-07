"""django_site URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import path, include

from django.urls import include, path, re_path
from django.views.i18n import JavaScriptCatalog
from django.views.static import serve
from django.contrib.auth.decorators import login_required

from django.shortcuts import redirect, render
from drf_yasg.generators import OpenAPISchemaGenerator
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from utils.errors import SystemRunningError
from utils.permissions import APIIPPermission
from version import __version__, __version_git_change_set__

from . import admin_site  # admin后台一些设置


def home(request):
    return redirect(to='vms:vms-list')


def about(request):
    return render(request, 'about.html',
                  context={'version': __version__, 'version_git_change_set': __version_git_change_set__})


def app_nav(request):
    return render(request, 'app_nav.html')


def custom_500(request, *args, **argv):
    error = SystemRunningError()
    return error.render(request=request)


class BothHttpAndHttpsSchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema.schemes = ["http", "https"]
        return schema


schema_view = get_schema_view(
    openapi.Info(
        title="EVCloud API",
        default_version='v3',
    ),
    public=False,
    generator_class=BothHttpAndHttpsSchemaGenerator,
    permission_classes=[permissions.IsAuthenticated, APIIPPermission]
)

urlpatterns = [
    path('', home, name='home'),
    # path('admin/', admin.site.urls),
    path('users/', include('users.urls', namespace='users')),
    path('api/v3/', include('api.urls', namespace='api')),
    path('vms/', include('vms.urls', namespace='vms')),
    path('vdisk/', include('vdisk.urls', namespace='vdisk')),
    path('device/', include('device.urls', namespace='device')),
    # path('novnc/', include('novnc.urls', namespace='novnc')),
    path('network/', include('network.urls', namespace='network')),
    path('image/', include('image.urls', namespace='image')),
    path('reports/', include('reports.urls', namespace='reports')),
    path('vpn/', include('vpn.urls', namespace='vpn')),
    path('apidocs/', schema_view.with_ui('swagger', cache_timeout=0), name='apidocs'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='redoc'),
    path('docs/', include('docs.urls', namespace='docs')),
    path('about/', about, name='about'),
    path('appnav/', login_required(app_nav), name='appnav'),
    path('pcservers/', include('pcservers.urls', namespace='compute')),
    path('log/', include('logrecord.urls', namespace='log-record')),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    path("i18n/", include("django.conf.urls.i18n")),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),

]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
                      path('__debug__/', include(debug_toolbar.urls)),

                      # For django versions before 2.0:
                      # url(r'^__debug__/', include(debug_toolbar.urls)),

                  ] + urlpatterns

if not settings.DEBUG:
    handler500 = 'django_site.urls.custom_500'
