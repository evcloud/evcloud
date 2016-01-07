#coding=utf-8
from django.http import  HttpResponse
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.conf import settings
from novnc.vnc import VNC

def vnc_view(req):
    vncid = req.GET.get("vncid")
    close = req.GET.get('close')
    if not vncid:
        return HttpResponse('error.')
    
    vncmamanger = VNC() 
    if close:
        vncmamanger.del_token(vncid)
        return HttpResponse('<script language="javascript">window.close();</script>VNC链接成功关闭。')
        
    else:
        dic = {'vncid': vncid}
        dic['url'] = 'http://%(host)s:%(port)d/vnc_auto.html?path=websockify/?token=%(vncid)s' % {
            'host': settings.NOVNC_HOST,
            'port': settings.NOVNC_PORT,
            'vncid': vncid
            }
        
        return render_to_response('novnc.html', dic, context_instance=RequestContext(req)) 