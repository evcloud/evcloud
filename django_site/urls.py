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
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from rest_framework_swagger.views import get_swagger_view

admin.AdminSite.site_header = 'EVCloud后台管理（管理员登录）'
admin.AdminSite.site_title = '管理员登录'

def home(request):
    return redirect(to='vms:vms-list')

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('users/', include('users.urls', namespace='users')),
    path('api/', include('api.urls', namespace='api')),
    path('vms/',include('vms.urls', namespace='vms')),
    path('vdisk/',include('vdisk.urls', namespace='vdisk')),
    path('novnc/',include('novnc.urls', namespace='novnc')),
    path('network/',include('network.urls', namespace='network')),
    path('apidocs/', get_swagger_view(title='EVCloud API'), name='apidocs'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),

        # For django versions before 2.0:
        # url(r'^__debug__/', include(debug_toolbar.urls)),

    ] + urlpatterns



