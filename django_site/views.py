import json
from django.views import View
from django.http import JsonResponse


class SetTimezoneView(View):

    def post(self, request):
        default_timezone = 'UTC'
        use_timezone = request.POST.get('timezone', None)
        if use_timezone is None or use_timezone == default_timezone:
            request.session['useTimeZone'] = default_timezone
            return JsonResponse({'timezone': default_timezone}, status=200)

        # 保存用户的时区到 session 中
        request.session['useTimeZone'] = use_timezone

        return JsonResponse({'timezone': use_timezone}, status=200)
