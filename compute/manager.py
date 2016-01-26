#coding=utf-8
import libvirt
from api.error import Error
from api.error import ERR_HOST_CONNECTION
from .host import host_alive
class VirtManager(object):
    def _connection(self, host):
        error = ''
        if not host:
            try:
                conn = libvirt.open("qemu:///system")
            except Exception as e:
                error = e
            else:
                return conn
        else:
#             if self.hostmanager.host_alive(host):
            if host_alive(host):
                try:
                    conn = libvirt.open("qemu+ssh://%s/system" % host)
                except Exception as e:
                    error = e
                else:
                    return conn
            
        raise Error(ERR_HOST_CONNECTION)