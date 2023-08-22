from urllib import parse
from django.urls import reverse
from . import MyAPITestCase, get_or_create_user, get_or_create_pci, get_or_create_center, get_or_create_group, \
    get_or_create_host


class pciTests(MyAPITestCase):
    """宿主机组列表 测试"""

    def setUp(self) -> None:
        self.user = get_or_create_user()
        self.host = get_or_create_host(ipv4='192.168.222.1', pcserver_host_ipv4='192.168.222.1')
        self.pci1 = get_or_create_pci(host=self.host)

    def test_list_pci(self):
        self.client.force_login(self.user)
        url = reverse('api:pci-device-list')
        response = self.client.get(url)
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'type', 'vm', 'host', 'attach_time', 'remarks'], response.data['results'][0])

        self.assertKeysIn(
            ['val', 'name'], response.data['results'][0]['type'])

        self.assertKeysIn(
            ['id', 'ipv4'], response.data['results'][0]['host'])

        self.center = get_or_create_center()
        query = parse.urlencode(query={'center_id': self.center.id})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'type', 'vm', 'host', 'attach_time', 'remarks'], response.data['results'][0])

        self.assertKeysIn(
            ['val', 'name'], response.data['results'][0]['type'])

        self.assertKeysIn(
            ['id', 'ipv4'], response.data['results'][0]['host'])

        self.group = get_or_create_group(name=self.pci1.host.group.name)
        print(self.pci1.host.ipv4, self.pci1.host.group.id, self.group.id)
        query = parse.urlencode(query={'group_id': self.group.id})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'type', 'vm', 'host', 'attach_time', 'remarks'], response.data['results'][0])

        self.assertKeysIn(
            ['val', 'name'], response.data['results'][0]['type'])

        self.assertKeysIn(
            ['id', 'ipv4'], response.data['results'][0]['host'])

        query = parse.urlencode(query={'group_id': 50})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['err_code'], 'Error')

        query = parse.urlencode(query={'host_id': self.host.id})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'type', 'vm', 'host', 'attach_time', 'remarks'], response.data['results'][0])

        self.assertKeysIn(
            ['val', 'name'], response.data['results'][0]['type'])

        self.assertKeysIn(
            ['id', 'ipv4'], response.data['results'][0]['host'])

        query = parse.urlencode(query={'host_id': 50})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['err_code'], 'Error')

        query = parse.urlencode(query={'type': self.pci1.type})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'type', 'vm', 'host', 'attach_time', 'remarks'], response.data['results'][0])

        self.assertKeysIn(
            ['val', 'name'], response.data['results'][0]['type'])

        self.assertKeysIn(
            ['id', 'ipv4'], response.data['results'][0]['host'])

        query = parse.urlencode(query={'type': 10})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], [])

        query = parse.urlencode(query={'search': self.pci1.remarks})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'type', 'vm', 'host', 'attach_time', 'remarks'], response.data['results'][0])

        self.assertKeysIn(
            ['val', 'name'], response.data['results'][0]['type'])

        self.assertKeysIn(
            ['id', 'ipv4'], response.data['results'][0]['host'])

        query = parse.urlencode(query={'search': self.host.ipv4})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'type', 'vm', 'host', 'attach_time', 'remarks'], response.data['results'][0])

        self.assertKeysIn(
            ['val', 'name'], response.data['results'][0]['type'])

        self.assertKeysIn(
            ['id', 'ipv4'], response.data['results'][0]['host'])

        query = parse.urlencode(query={'search': '123'})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], [])

        query = parse.urlencode(query={'center_id': self.center.id, 'host_id': 23})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['err_code'], 'Error')

        query = parse.urlencode(query={'center_id': 11, 'host_id': 23})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['err_code'], 'Error')

        query = parse.urlencode(query={'center_id': 11, 'host_id': 23, 'group_id': self.group.id})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['err_code'], 'Error')

        query = parse.urlencode(
            query={'center_id': self.center.id, 'host_id': self.host.id, 'group_id': self.group.id, 'type': 10})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], [])


