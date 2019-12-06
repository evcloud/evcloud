#coding=utf-8
from django.http import  HttpResponse
from django.shortcuts import render, redirect
from django.conf import settings

from novnc.manager import NovncTokenManager

NOVNC_PORT = getattr(settings, 'NOVNC_SERVER_PORT', 80)

def vnc_view(req):
    vncid = req.GET.get("vncid")
    close = req.GET.get('close')
    if not vncid:
        return HttpResponse('error.')
    if close:
        vncmanager = NovncTokenManager() 
        vncmanager.del_token(vncid)
        return HttpResponse('<script language="javascript">window.close();</script>VNC链接成功关闭。')
    else:
        dic = {'vncid': vncid}
        http_host = req.META['HTTP_HOST']
        http_host = http_host.split(':')[0]

        if NOVNC_PORT == 80:
            dic['url'] = f'http://{http_host}/novnc_nginx/vnc_auto.html?path=websockify/?token={vncid}'
            return render(req, 'novnc.html', dic)

        http_host = f'{http_host}:{NOVNC_PORT}'
        url = f'http://{http_host}/vnc_auto.html?path=websockify/?token={vncid}'
        return redirect(to=url)


