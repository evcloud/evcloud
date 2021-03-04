from django.urls import path
from .views import vnc_view

app_name = 'novnc'

urlpatterns = [
    path(r'', vnc_view, name='vnc'),
]
