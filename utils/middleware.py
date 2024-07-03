from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from utils.permissions import APIIPRestrictor


class CloseCsrfMiddleware(MiddlewareMixin):

    def process_request(self, request):
        request.csrf_processing_done = True  # csrf处理完毕


class AdminIPRestrictMiddleware:
    admin_url = '/admin'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(self.admin_url):
            try:
                APIIPRestrictor().check_restricted(request=request)
            except Exception as e:
                return HttpResponseForbidden(f'{str(e)}')
        return self.get_response(request)
