from django.urls import path, include
from django.contrib.auth.decorators import login_required
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'log-record'

urlpatterns = [
    path('list/', login_required(views.LogRecordView.as_view()), name='log-record-list'),
]
