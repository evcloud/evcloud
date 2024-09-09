import json
from django.views import View
from django.http import JsonResponse


class SetTimezoneView(View):

    def post(self, request):
        use_timezone = 'UTC'

        # 获取原始请求体数据
        raw_data = request.body

        if not raw_data:
            return JsonResponse({'error': 'body is null'}, status=400)

        # 将字节数据解码为字符串，例如 UTF-8
        try:
            decoded_data = raw_data.decode('utf-8')
        except UnicodeDecodeError:
            return JsonResponse({'error': 'Unable to decode data'}, status=400)

        try:
            json_data = json.loads(decoded_data)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        if json_data['timezone']:
            use_timezone = json_data['timezone']

        # 保存用户的时区到 session 中
        request.session['useTimeZone'] = use_timezone

        return JsonResponse({'status': 'success'})
