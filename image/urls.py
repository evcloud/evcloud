from django.urls import path, re_path
from django.contrib.auth.decorators import login_required

from . import views

app_name = 'image'

urlpatterns = [
    path('', login_required(views.ImageView.as_view()), name='image-list'),
    path('add/', login_required(views.ImageAddView.as_view()), name='image-add'),
    path('change/<int:id>/', login_required(views.ImageChangeView.as_view()), name='image-change'),
    path('delete/<int:id>/', login_required(views.ImageDeleteView.as_view()), name='image-delete'),

    path('create-image-vm/<int:image_id>/', login_required(views.ImageVmCreateView.as_view()), name='image-vm-create'),
    path('image-vm-operate/', login_required(views.ImageVmOperateView.as_view()), name='image-vm-operate'),

]
