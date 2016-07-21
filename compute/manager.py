#coding=utf-8
import libvirt
import subprocess
from api.error import Error
from api.error import ERR_HOST_CONNECTION
from api.error import ERR_VM_UUID
from api.error import ERR_VM_MISSING
from api.error import ERR_GROUP_ID
import xml.dom.minidom

from .models import Center as DBCenter
from .center import Center
from .models import Group as DBGroup
from .group import Group

class CenterManager(object):
    def center_id_exists(self, center_id):
        return DBCenter.objects.filter(pk=center_id).exists()

    def get_center_by_id(self, center_id):
        center = DBCenter.objects.filter(id = center_id)
        if not center.exists():
            return False
        center = center[0]
        return self._get_center_data(center)

    def get_center_list(self):
        centers = DBCenter.objects.all().order_by('order')
        ret_list = []
        for center in centers:
            ret_list.append(self._get_center_data(center))
        return ret_list

    def get_center_list_in_perm(self, user):
        centers = DBCenter.objects.all().order_by('order')
        ret_list = []
        for center in centers:
            c = self._get_center_data(center)
            if c.managed_by(user):
                ret_list.append(c)
        return ret_list        

    def _get_center_data(self, center):
        if type(center) != DBCenter:
            return False
        return Center(center)

class GroupManager(object):
    def get_group_list(self, center_id=None):
        if center_id == None:
            groups = DBGroup.objects.all()
        else:
            groups = DBGroup.objects.filter(center_id = center_id)
        groups = groups.order_by('order')
        ret_list = []
        for group in groups:
            ret_list.append(self._get_group_data(group))
        return ret_list

    def get_group_list_by_user(self, user, center_id = None):
        if center_id == None:
            groups = DBGroup.objects.filter(admin_user = user)
        else:
            groups = DBGroup.objects.filter(admin_user = user, center_id = center_id)
        groups = groups.order_by('order')
        ret_list = []
        for group in groups:
            ret_list.append(self._get_group_data(group))
        return ret_list

    def get_group_by_id(self, group_id):
        group = DBGroup.objects.filter(id = group_id)
        if not group.exists():
            raise Error(ERR_GROUP_ID)
        return self._get_group_data(group[0])

    def has_center_perm(self, user, center_id):
        '''对指定center有部分或全部管理权，即对该分中心中的 某个集群有管理权,则返回True'''
        return DBGroup.objects.filter(admin_user = user, center_id = center_id).exists()


    def _get_group_data(self, group):
        if not type(group) == DBGroup:
            return False
        return Group(group)

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
