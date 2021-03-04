from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'image'

urlpatterns = [
    path('', login_required(views.ImageView.as_view()), name='image-list'),
]
