#coding=utf-8

from django.utils.deprecation import MiddlewareMixin
from .models import SiteConfig

class SiteConfigMiddleware(MiddlewareMixin):
    def process_request(self,request):
        site_conf = {"name":"EVCloud","pro_enable":False} 
        if SiteConfig.objects.count() > 0:
            obj = SiteConfig.objects.first()
            site_conf['name'] = obj.name
            site_conf['pro_enable'] = obj.pro_enable
        request.site_conf = site_conf


        