from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView

from . import views

app_name = 'users'

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name="logout"),

    path('register/', views.register_user, name='register'),
    path('change_password/', views.change_password, name='change_password'),
    path('active/', views.active_user, name='active'),
    # path('forget/', views.forget_password, name='forget'),
    # path('fconfirm/', views.forget_password_confirm, name='forget_confirm'),
    # path('security/', views.security, name='security')
]
