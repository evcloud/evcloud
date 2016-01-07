from django.conf.urls import include, url
#from views import root, index
from views import  index, alloclist, alloc_center, alloc_group

urlpatterns = [
    url(r'^$', index),
    #url(r'^(?P<url>.+)', root),
    url(r'^alloclist/',alloclist),
    url(r'^center/',alloc_center),
    url(r'^group/',alloc_group),

]
