from django.conf.urls import include, url
from .views import *

app_name = 'novnc'

urlpatterns = [
    url(r'^.*', vnc_view),
]