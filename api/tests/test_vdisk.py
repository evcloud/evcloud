import uuid
from urllib import parse
from django.urls import reverse
from . import MyAPITestCase, get_or_create_user, get_or_create_ceph_pool_vdisk, get_or_create_vdisk, get_or_create_vm, \
    get_or_create_macip, get_or_create_host


class vdiskTests(MyAPITestCase):
    """云硬盘测试 测试"""

    def setUp(self) -> None:
        self.user = get_or_create_user()
        self.vdisk_ceph_pool = get_or_create_ceph_pool_vdisk()
        self.vdisk_ceph_pool2 = get_or_create_ceph_pool_vdisk()
        self.uuid_str = uuid.uuid4()
        self.uuid_str2 = uuid.uuid4()
        self.vdisk = get_or_create_vdisk(uuid=self.uuid_str, quota=self.vdisk_ceph_pool, remarks='test vdisk')
        self.vdisk2 = get_or_create_vdisk(uuid=self.uuid_str2, quota=self.vdisk_ceph_pool2, remarks='test vdisk2')

    def test_list_quota(self):
        self.client.force_login(self.user)
        url = reverse('api:quota-list')
        response = self.client.get(url)
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'pool', 'ceph', 'group', 'total', 'size_used', 'max_vdisk', 'enable'],
            response.data['results'][0])

        self.assertKeysIn(['id', 'name', 'enable'], response.data['results'][0]['pool'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['ceph'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['group'])

        query = parse.urlencode(query={'group_id': self.vdisk_ceph_pool.group_id})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'pool', 'ceph', 'group', 'total', 'size_used', 'max_vdisk', 'enable'],
            response.data['results'][0])

        self.assertKeysIn(['id', 'name', 'enable'], response.data['results'][0]['pool'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['ceph'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['group'])

        query = parse.urlencode(query={'group_id': 100})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], [])

        query = parse.urlencode(query={'group_id': '100'})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], [])

        query = parse.urlencode(query={'enable': 'true'})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'pool', 'ceph', 'group', 'total', 'size_used', 'max_vdisk', 'enable'],
            response.data['results'][0])

        self.assertKeysIn(['id', 'name', 'enable'], response.data['results'][0]['pool'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['ceph'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['group'])
        self.assertEqual(response.data['results'][0]['pool']['enable'], True)

        self.vdisk_ceph_pool.enable = False
        self.vdisk_ceph_pool.save(update_fields=['enable'])
        query = parse.urlencode(query={'enable': 'false'})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'pool', 'ceph', 'group', 'total', 'size_used', 'max_vdisk', 'enable'],
            response.data['results'][0])

        self.assertKeysIn(['id', 'name', 'enable'], response.data['results'][0]['pool'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['ceph'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['group'])
        self.assertEqual(response.data['results'][0]['pool']['enable'], False)

        query = parse.urlencode(query={'enable': 'false', 'group_id': self.vdisk_ceph_pool.group_id})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'pool', 'ceph', 'group', 'total', 'size_used', 'max_vdisk', 'enable'],
            response.data['results'][0])

        self.assertKeysIn(['id', 'name', 'enable'], response.data['results'][0]['pool'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['ceph'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['group'])
        self.assertEqual(response.data['results'][0]['pool']['enable'], False)

        query = parse.urlencode(query={'enable': 'false', 'group_id': 100})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], [])

    def test_list_vdisk(self):
        """云硬盘列表"""

        self.client.force_login(self.user)
        url = reverse('api:vdisk-list')
        response = self.client.get(url)
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['uuid', 'size', 'vm', 'user', 'quota', 'create_time', 'attach_time', 'enable', 'remarks', 'group'],
            response.data['results'][0])

        self.assertKeysIn(['id', 'username'], response.data['results'][0]['user'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['quota'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['group'])

        # center_id
        query = parse.urlencode(query={'center_id': self.vdisk.quota.group.center_id})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['uuid', 'size', 'vm', 'user', 'quota', 'create_time', 'attach_time', 'enable', 'remarks', 'group'],
            response.data['results'][0])

        self.assertKeysIn(['id', 'username'], response.data['results'][0]['user'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['quota'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['group'])

        # group_id
        query = parse.urlencode(query={'group_id': self.vdisk.quota.group_id})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['uuid', 'size', 'vm', 'user', 'quota', 'create_time', 'attach_time', 'enable', 'remarks', 'group'],
            response.data['results'][0])

        self.assertKeysIn(['id', 'username'], response.data['results'][0]['user'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['quota'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['group'])

        # quota_id
        query = parse.urlencode(query={'quota_id': self.vdisk.quota_id})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['uuid', 'size', 'vm', 'user', 'quota', 'create_time', 'attach_time', 'enable', 'remarks', 'group'],
            response.data['results'][0])

        self.assertKeysIn(['id', 'username'], response.data['results'][0]['user'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['quota'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['group'])

        # user_id
        query = parse.urlencode(query={'user_id': self.vdisk.user_id})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['uuid', 'size', 'vm', 'user', 'quota', 'create_time', 'attach_time', 'enable', 'remarks', 'group'],
            response.data['results'][0])

        self.assertKeysIn(['id', 'username'], response.data['results'][0]['user'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['quota'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['group'])

        # search --> uuid、remarks
        query = parse.urlencode(query={'search': self.uuid_str})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['uuid', 'size', 'vm', 'user', 'quota', 'create_time', 'attach_time', 'enable', 'remarks', 'group'],
            response.data['results'][0])

        self.assertKeysIn(['id', 'username'], response.data['results'][0]['user'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['quota'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['group'])

        query = parse.urlencode(query={'search': 'test'})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['uuid', 'size', 'vm', 'user', 'quota', 'create_time', 'attach_time', 'enable', 'remarks', 'group'],
            response.data['results'][0])

        self.assertKeysIn(['id', 'username'], response.data['results'][0]['user'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['quota'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['group'])

        query = parse.urlencode(query={'search': 'vdisk'})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['uuid', 'size', 'vm', 'user', 'quota', 'create_time', 'attach_time', 'enable', 'remarks', 'group'],
            response.data['results'][0])

        self.assertKeysIn(['id', 'username'], response.data['results'][0]['user'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['quota'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['group'])

        query = parse.urlencode(query={'mounted': 'false'})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['uuid', 'size', 'vm', 'user', 'quota', 'create_time', 'attach_time', 'enable', 'remarks', 'group'],
            response.data['results'][0])

        self.assertKeysIn(['id', 'username'], response.data['results'][0]['user'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['quota'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['group'])

        vm_uuid = uuid.uuid4()
        mac_ip = get_or_create_macip(ipv4='192.168.222.2', used=True)
        host = get_or_create_host(ipv4='192.168.222.1', pcserver_host_ipv4='192.168.222.1')
        self.vm = get_or_create_vm(uuid=vm_uuid, mac_ip=mac_ip, host=host)

        self.vdisk.vm = self.vm
        self.vdisk.dev = 'vdb'
        self.vdisk.save(update_fields=['vm', 'dev'])

        query = parse.urlencode(query={'mounted': 'true'})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['uuid', 'size', 'vm', 'user', 'quota', 'create_time', 'attach_time', 'enable', 'remarks', 'group'],
            response.data['results'][0])

        self.assertKeysIn(['id', 'username'], response.data['results'][0]['user'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['quota'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['group'])
        self.assertKeysIn(['uuid', 'ipv4', 'ipv6'], response.data['results'][0]['vm'])

    def test_list_vdisk_uuid(self):
        self.client.force_login(self.user)

        url = reverse('api:vdisk-detail', kwargs={'uuid': self.vdisk.uuid})
        response = self.client.get(url)
        print(response.data)
        self.assertEqual(response.status_code, 200)

        self.assertKeysIn(
            ['uuid', 'size', 'vm', 'dev', 'user', 'quota', 'create_time', 'attach_time', 'enable', 'remarks'],
            response.data['vm'])
        self.assertKeysIn(['id', 'username'], response.data['vm']['user'])
        self.assertKeysIn(['id', 'name', 'pool', 'ceph', 'group'], response.data['vm']['quota'])
        self.assertKeysIn(['id', 'name', 'enable'], response.data['vm']['quota']['pool'])
        self.assertKeysIn(['id', 'name'], response.data['vm']['quota']['ceph'])
        self.assertKeysIn(['id', 'name'], response.data['vm']['quota']['group'])

        vm_uuid = uuid.uuid4()
        mac_ip = get_or_create_macip(ipv4='192.168.222.2', used=True)
        host = get_or_create_host(ipv4='192.168.222.1', pcserver_host_ipv4='192.168.222.1')
        self.vm = get_or_create_vm(uuid=vm_uuid, mac_ip=mac_ip, host=host)

        self.vdisk.vm = self.vm
        self.vdisk.dev = 'vdb'
        self.vdisk.save(update_fields=['vm', 'dev'])

        response = self.client.get(url)
        print(response.data)
        self.assertEqual(response.status_code, 200)

        self.assertKeysIn(
            ['uuid', 'size', 'vm', 'dev', 'user', 'quota', 'create_time', 'attach_time', 'enable', 'remarks'],
            response.data['vm'])
        self.assertKeysIn(['id', 'username'], response.data['vm']['user'])
        self.assertKeysIn(['id', 'name', 'pool', 'ceph', 'group'], response.data['vm']['quota'])
        self.assertKeysIn(['id', 'name', 'enable'], response.data['vm']['quota']['pool'])
        self.assertKeysIn(['id', 'name'], response.data['vm']['quota']['ceph'])
        self.assertKeysIn(['id', 'name'], response.data['vm']['quota']['group'])
        self.assertKeysIn(['uuid', 'ipv4', 'ipv6'], response.data['vm']['vm'])
