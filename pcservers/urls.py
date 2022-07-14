from django.urls import path
from django.contrib.auth.decorators import login_required

from pcservers import views

app_name = 'pcservers'

urlpatterns = [
    path('', login_required(views.get_pc_server_by_id), name='get_pcserver_by_id')
]
