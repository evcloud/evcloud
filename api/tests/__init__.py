from rest_framework.test import APITestCase

from compute.models import Host, Group
from pcservers.models import PcServer, Room, ServerType
from users.models import UserProfile
from ceph.models import CephCluster, CephPool, Center
from image.models import VmXmlTemplate, Image

from django_site.test_settings import *


def get_or_create_user(username='test', password='password') -> UserProfile:
    user, created = UserProfile.objects.get_or_create(username=username, password=password, is_active=True)
    return user


def get_or_create_center(name: str = 'test'):
    c = Center.objects.filter(name=name).first()
    if c is not None:
        return c

    c = Center(name=name, location=name, desc=name)
    c.save(force_insert=True)
    return c


def get_or_create_ceph(name: str = 'test'):
    c = CephCluster.objects.filter(name=name).first()
    if c is not None:
        return c

    center = get_or_create_center()
    c = CephCluster(
        id=100,
        name=name, center_id=center.id, has_auth=True,
        uuid=cephuuid, config=cephconfig,
        config_file=config_file,
        keyring=keyring, keyring_file=keyring_file, hosts_xml=host_xml,
        username='admin'
    )
    c.save(force_insert=True)
    return c


def get_or_create_ceph_pool(name: str = 'test'):
    cp = CephPool.objects.filter(pool_name=name).first()
    if cp is not None:
        return cp

    ceph = get_or_create_ceph()
    cp = CephPool(pool_name=name, ceph=ceph)
    cp.save(force_insert=True)
    return cp


def get_or_create_xml_temp(name: str = 'test'):
    t = VmXmlTemplate.objects.filter(name=name).first()
    if t is not None:
        return t

    t = VmXmlTemplate(
        name=name, xml=''
    )
    t.save(force_insert=True)
    return t


def get_or_create_image(name: str = 'test_image', user=None):
    queryset = Image.objects.filter(name=name).first()
    if queryset is not None:
        return queryset

    pool = get_or_create_ceph_pool()
    temp = get_or_create_xml_temp()
    image = Image(
        name=name,
        sys_type=Image.SYS_TYPE_LINUX,
        version='系统版本信息',
        ceph_pool=pool,
        tag=Image.TAG_USER,
        user=user,
        xml_tpl=temp,
        size=10,
        desc='系统镜像测试'
    )
    super(Image, image).save(force_insert=True)

    return image


def get_or_create_room(name: str = 'test_room'):
    queryset = Room.objects.filter(name=name).first()
    if queryset is not None:
        return queryset

    room = Room(
        name=name,
        city=name,
        desc=name
    )
    room.save(force_insert=True)
    return room


def get_or_create_servertype(name: str = 'test_servertype'):
    queryset = ServerType.objects.filter(name=name).first()
    if queryset is not None:
        return queryset

    servertype = ServerType(
        name=name,
        desc=name
    )
    servertype.save(force_insert=True)
    return servertype


def get_or_create_pcserver(host_ipv4='127.0.0.1', roon_name=None, servertype_name=None):
    """服务器"""
    queryset = PcServer.objects.filter(host_ipv4=host_ipv4).first()
    if queryset is not None:
        return queryset

    user = get_or_create_user()
    if roon_name:
        room = get_or_create_room(name=roon_name)
    else:
        room = get_or_create_room()

    if servertype_name:
        servertype = get_or_create_servertype(name=servertype_name)
    else:
        servertype = get_or_create_servertype()

    pcserver = PcServer(
        room=room,
        server_type=servertype,
        status=1,
        tag_no='testxxx',
        location='testxxx',
        host_ipv4=host_ipv4,
        ipmi_ip='127.0.0.1',
        user=user,

    )
    pcserver.save(force_insert=True)
    return pcserver


def get_or_create_group(name: str = 'test_group', center_name=None, ):
    queryset = Group.objects.filter(name=name).first()
    if queryset is not None:
        return queryset

    if center_name:

        center = get_or_create_center(name=center_name)
    else:
        center = get_or_create_center()

    user = get_or_create_user()

    group = Group(
        center=center,
        name=name,
        enable=True,
        desc='',
    )
    group.save(force_insert=True)
    group.users.add(user)
    return group


def get_or_create_host(ipv4='127.0.0.1', real_cpu=8, real_mem=8, vm_limit=5, group_name=None,
                       pcserver_host_ipv4=None):
    queryset = Host.objects.filter(ipv4=ipv4).first()
    if queryset is not None:
        return queryset
    if group_name:
        group = get_or_create_group(name=group_name)
    else:
        group = get_or_create_group()

    if pcserver_host_ipv4:

        pcserver = get_or_create_pcserver(host_ipv4=pcserver_host_ipv4)
    else:
        pcserver = get_or_create_pcserver()

    host = Host(
        group=group,
        pcserver=pcserver,
        ipv4=ipv4,
        real_cpu=real_cpu,
        real_mem=real_mem,
        vcpu_total=16,
        vcpu_allocated=0,
        mem_total=16,
        mem_allocated=0,
        vm_limit=vm_limit,
        vm_created=0,
    )
    host.save(force_insert=True)
    return host


class MyAPITestCase(APITestCase):
    def assertKeysIn(self, keys: list, container):
        for k in keys:
            self.assertIn(k, container)

    def assertErrorResponse(self, status_code: int, code: str, response):
        self.assertEqual(response.status_code, status_code)
        self.assertKeysIn(['code', 'message'], response.data)
        self.assertEqual(response.data['code'], code)

    def assert_is_subdict_of(self, sub: dict, d: dict):
        for k, v in sub.items():
            if k in d and v == d[k]:
                continue
            else:
                self.fail(f'{sub} is not sub dict of {d}, Not Equal key is {k}, {v} != {d.get(k)}')

        return True
