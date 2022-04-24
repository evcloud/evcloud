from rest_framework.test import APITestCase

from users.models import UserProfile
from ceph.models import CephCluster, CephPool, Center
from image.models import VmXmlTemplate


def get_or_create_user(username='test', password='password') -> UserProfile:
    user, created = UserProfile.objects.get_or_create(username=username, password=password, is_active=True)
    return user

def get_or_create_center(name: str = 'test'):
    c = Center.objects.filter(name=name).first()
    if c is not None:
        return c

    c = Center(name=name)
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
        uuid='test', config='', config_file='',
        keyring='', keyring_file='', hosts_xml=''
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
