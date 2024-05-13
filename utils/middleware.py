from django.utils.deprecation import MiddlewareMixin
from rest_framework.authentication import SessionAuthentication


class CloseCsrfMiddleware(MiddlewareMixin):

    def process_request(self, request):
        request.csrf_processing_done = True  # csrf处理完毕


# class CustomSessionAuthentication(SessionAuthentication):
#
#     def enforce_csrf(self, request):
#         # 禁用 CSRF 验证
#        return
