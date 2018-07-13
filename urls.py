from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.views.static import serve

from django.contrib.auth.views import login, logout
from vmadmin.admin import admin_site
from vmadmin.vm_views import index_view

from django.views.generic import TemplateView

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='help.html')),
    url(r'^admin/', include(admin_site.urls)),
    url(r'^api/v1/', include('api.urls')),
    url(r'^api/v2/', include('api.urls_v2')),
    url(r'^vnc/', include('novnc.urls')),
    url(r'^vmadmin/', include('vmadmin.urls')),
    url(r'^reports/', include('reports.urls')),
    url(r'^accounts/login/$',  login, {'template_name':'login.html'}), 
    url(r'^accounts/logout/$', logout),
    # url(r'^help/$', TemplateView.as_view(template_name='help.html')),
]

urlpatterns += [
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
]

urlpatterns += [
    url(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
]

