#coding=utf-8
import libvirt
import subprocess
from api.error import Error
from api.error import ERR_HOST_CONNECTION
from api.error import ERR_VM_UUID
from api.error import ERR_VM_MISSING
import xml.dom.minidom

class XMLEditor(object):
    def set_xml(self, xml_desc):
        try:
            self._dom = xml.dom.minidom.parseString(xml_desc)
        except Exception as e:
            return False
        else:
            return True

    def get_dom(self):
        if self._dom:
            return self._dom
        return None

    def get_root(self):
        if self._dom:
            return self._dom.documentElement
        return None

    def get_node(self, path):
        node = self._dom.documentElement
        for tag in path:
            find = False
            for child_node in node.childNodes:
                if child_node.nodeName == tag:
                    find = True
                    node = child_node
                    break
            if not find:
                return None
        return node

class VirtManager(object):
    def _host_alive(self, host_ipv4, times=3):
        cmd = 'fping %s -r %d' % (host_ipv4, times)
        res, info = subprocess.getstatusoutput(cmd)
        # print(cmd, res)
        if res == 0:
            return True
        return False

    def _get_connection(self, host):
        error = ''
        if not host:
            try:
                conn = libvirt.open("qemu:///system")
            except Exception as e:
                error = e
            else:
                return conn
        else:
            if self._host_alive(host):
                try:
                    conn = libvirt.open("qemu+ssh://%s/system" % host)
                except Exception as e:
                    error = e
                else:
                    return conn
            
        raise Error(ERR_HOST_CONNECTION)

    def define(self, host_ipv4, xml_desc):
        conn = self._get_connection(host_ipv4)
        try:
            dom = conn.defineXML(xml_desc)
            # print(dom)
        except Exception as e:
            print(e)
            raise Error(ERR_VM_DEFINE)
        return dom

    def get_domain(self, host_ipv4, vm_uuid):
        conn = self._get_connection(host_ipv4)
        for d in conn.listAllDomains():
            if d.UUIDString() == vm_uuid:
                return d
        raise Error(ERR_VM_MISSING)

    def domain_exists(self, host_ipv4, vm_uuid):
        conn = self._get_connection(host_ipv4)
        for d in conn.listAllDomains():
            if d.UUIDString() == vm_uuid:
                return True
        return False


    def undefine(self, host_ipv4, vm_uuid):
        dom = self.get_domain(host_ipv4, vm_uuid)
        if dom.undefine() == 0:
            return True
        return False

    def _xml_edit_vcpu(self, xml_desc, vcpu):
        xml = XMLEditor()
        xml.set_xml(xml_desc)
        root = xml.get_root()
        try:
            root.getElementsByTagName('vcpu')[0].firstChild.data = vcpu
        except:
            return False
        return root.toxml()

    def _xml_edit_mem(self, xml_desc, mem):
        xml = XMLEditor()
        xml.set_xml(xml_desc)
        try:
            node = xml.get_node([ 'memory'])
            if node:
                node.attributes['unit'].value = 'MiB'
                node.firstChild.data = mem
            node1 = xml.get_node(['currentMemory'])
            if node1:
                node1.attributes['unit'].value = 'MiB'
                node1.firstChild.data = mem
            return xml.get_root().toxml()
        except:
            return False
