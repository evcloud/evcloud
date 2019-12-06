from django.urls import path
from .views import docs

app_name = 'docs'

urlpatterns = [
    path('', docs, name='docs'),
]
