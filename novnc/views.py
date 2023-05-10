# coding=utf-8
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.conf import settings

from novnc.manager import NovncTokenManager

NOVNC_PORT = getattr(settings, 'NOVNC_SERVER_PORT', 80)


def vnc_view(req):
    vncid = req.GET.get("vncid")
    protocol_type = req.GET.get("type", 'vnc')
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
        http_scheme = 'https'

        global_config_obj = GlobalConfig().get_global_config()
        if global_config_obj:
            http_scheme = global_config_obj.novnchttp

        if NOVNC_PORT == 80:
            if protocol_type == 'spice':
                dic['url'] = f'{http_scheme}://{http_host}/novnc_nginx/spice/spice_auto.html?path=websockify/?token={vncid}'
            else:
                dic['url'] = f'{http_scheme}://{http_host}/novnc_nginx/novnc/vnc_lite.html?path=websockify/?token={vncid}'

            return render(req, 'novnc.html', dic)

        http_host = f'{http_host}:{NOVNC_PORT}'
        if protocol_type == 'spice':
            url = f'{http_scheme}://{http_host}/spice/spice_auto.html?path=websockify/?token={vncid}'
        else:
            url = f'{http_scheme}://{http_host}/novnc/vnc_lite.html?path=websockify/?token={vncid}'

        return redirect(to=url)
