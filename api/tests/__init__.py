import datetime
import uuid
from rest_framework.test import APITestCase

from compute.models import Host, Group
from device.models import PCIDevice
from network.models import MacIP, Vlan
from pcservers.models import PcServer, Room, ServerType
from users.models import UserProfile
from ceph.models import CephCluster, CephPool, Center
from image.models import VmXmlTemplate, Image

from django_site.test_settings import *
from vms.models import Flavor, Vm


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


def get_or_create_host(ipv4: str = '127.0.0.1', real_cpu=8, real_mem=8, vm_limit=5, group_name=None,
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


def get_or_create_flavor(public: bool = True):
    queryset = Flavor.objects.filter(public=public).first()
    if queryset is not None:
        return queryset

    flavor = Flavor(
        vcpus=1,
        ram=2,
        public=public,
        enable=True
    )
    flavor.save(force_insert=True)
    return flavor


def get_or_create_vlan(br: str = 'test_br', tag: int = 0, group_name=None, subnet_ip: str = '192.168.1.1',
                       gateway: str = '192.168.1.243'):
    queryset = Vlan.objects.filter(br=br).first()
    if queryset is not None:
        return queryset

    if group_name:
        group = get_or_create_group(name=group_name)
    else:
        group = get_or_create_group()

    vlan = Vlan(
        br=br,
        name='test',
        group=group,
        tag=tag,
        subnet_ip=subnet_ip,
        net_mask='255.255.255.0',
        gateway=gateway,
        dns_server='114.114.114.114',
        dhcp_config='#'
    )
    vlan.save(force_insert=True)
    return vlan


def get_or_create_macip(ipv4: str = '127.0.0.1', mac: str = 'EC:BB:36:62:4C:46', vlan=None, used: bool = False):
    queryset = MacIP.objects.filter(ipv4=ipv4).first()
    if queryset is not None:
        return queryset

    if vlan is None:
        vlan = get_or_create_vlan()

    macip = MacIP(
        vlan=vlan,
        mac=mac,
        ipv4=ipv4,
        used=used,
    )
    macip.save(force_insert=True)
    return macip


def get_or_create_pci(address='/dev/sdb', type: int = 4, host=None, vm=None):
    queryset = PCIDevice.objects.filter(type=type).first()
    if queryset is not None:
        return queryset

    if host is None:
        host = get_or_create_host()

    attach_time = None
    if vm is not None:
        attach_time = datetime.datetime.now()

    pci_device = PCIDevice(
        type=type,
        vm=vm,
        attach_time=attach_time if attach_time else None,
        enable=True,
        host=host,
        address=address,
        remarks='test pci'

    )

    pci_device.save(force_insert=True)
    return pci_device


def get_or_create_vm(uuid, image=None, ceph_pool=None):
    queryset = Vm.objects.filter(uuid=uuid).first()
    if queryset is not None:
        return queryset

    user = get_or_create_user()

    if image is None:
        image = get_or_create_image()

    if ceph_pool is None:
        ceph_pool = get_or_create_ceph_pool()

    # vm_uuid = uuid.uuid4()
    vm = Vm(
        disk_type=Vm.DiskType.CEPH_RBD,
        sys_disk_size=10,
        uuid=uuid,
        name=uuid,
        vcpu=2,
        mem=2,
        disk=uuid,
        image=image,
        user=user,
        xml='#',
        image_name=image.name,
        image_parent=image.name,
        image_size=10,
        ceph_pool=ceph_pool,
    )
    vm.save(force_insert=True)
    return vm


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
