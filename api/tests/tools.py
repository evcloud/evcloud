#coding=utf-8
from django.contrib.auth.models import User
from compute.models import Center, Group, Host
from storage.models import CephHost, CephPool
from image.models import Image, ImageType, Xml
from network.models import Vlan, VlanType, MacIP

def create_user(user_name):
    u1 = User()
    u1.username = user_name
    u1.is_active = True
    u1.api_user = True
    u1.save()
    return u1

def create_superuser(user_name):
    u1 = User()
    u1.username = user_name
    u1.is_superuser = True
    u1.is_active = True
    u1.api_user = True
    u1.save()
    return u1

def create_center(name, location, desc):
    c1 = Center()
    c1.name = name
    c1.location = location
    c1.desc = desc
    c1.save()
    return c1

def create_group(center, name, desc, admin_user=[]):
    g1 = Group()
    g1.center = center
    g1.name = name
    g1.desc = desc
    g1.save()
    for u in admin_user:
        g1.admin_user.add(u)
    return g1

def create_ceph_host(center, ip, port, uuid):
    ch = CephHost()
    ch.center = center
    ch.host = ip
    ch.port = port
    ch.uuid = uuid
    ch.save()
    return ch

def create_ceph_image_pool(host, pool):
    cp = CephPool()
    cp.host = host
    cp.pool = pool
    cp.type = 1
    cp.save()
    return cp

def create_host(group, ip, enable=True, vlans=[]):
    h = Host()
    h.group = group
    h.ipv4 = ip
    h.enable = enable
    h.save()
    for v in vlans:
        h.vlan.add(v)
    return h

def create_imagetype(name):
    it = ImageType()
    it.name = name
    it.save()
    return it    

def create_xml(name, xml):
    x = Xml()
    x.name = name
    x.xml = xml
    x.save()
    return x 

def create_image(cp, xml, itype, name, version, snap, desc='', enable=True):  
    i = Image()
    i.cephpool = cp
    i.name = name
    i.version = version
    i.snap = snap
    i.desc = desc
    i.xml = xml
    i.type = itype
    i.enable = enable
    i.save()
    return i

def create_vlantype(name):
    vt = VlanType()
    vt.name = name
    vt.save()
    return vt

def create_vlan(vlan, br, vlan_type, enable=True):
    v = Vlan()
    v.vlan = vlan
    v.br = br
    v.type = vlan_type
    v.enable = enable
    v.save()
    return v
    
def create_ip(vlan, mac, ipv4):
    ip = MacIP()
    ip.vlan = vlan
    ip.mac = mac
    ip.ipv4 = ipv4
    ip.save()
    return ip