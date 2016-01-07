from django.conf.urls import include, url
from django.contrib import admin

from django.contrib.auth.views import login, logout
from vmadmin.admin import admin_site

urlpatterns = [
    url(r'^$', "vmadmin.views.index_view"),
    url(r'^admin/', include(admin_site.urls)),
    url(r'^api/v1/', include('api.urls')),
    url(r'^vnc/', include('novnc.urls')),
    url(r'^vmadmin/', include('vmadmin.urls')),
    url(r'^reports/', include('reports.urls')),
    url(r'^accounts/login/$',  login, {'template_name':'login.html'}), 
    url(r'^accounts/logout/$', logout),
]

