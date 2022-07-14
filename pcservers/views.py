import json
from datetime import datetime

from django.forms import model_to_dict
from django.http import HttpResponse
from .models import PcServer
from django.views.decorators.csrf import csrf_exempt


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return json.JSONEncoder.default(self, obj)

@csrf_exempt
def get_pc_server_by_id(request):
    server_id = request.GET['server_id']
    server = model_to_dict(PcServer.objects.get(id=server_id))
    return HttpResponse(json.dumps(server,cls=DateEncoder), content_type='application/json')
