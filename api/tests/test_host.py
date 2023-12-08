from urllib import parse
from django.urls import reverse
from . import MyAPITestCase, get_or_create_user, get_or_create_host


class hostTests(MyAPITestCase):
    """宿主机测试"""

    def setUp(self) -> None:
        self.user = get_or_create_user()
        self.host = get_or_create_host()

    def test_list_host(self):
        self.client.force_login(self.user)
        # 单位
        url = reverse('api:host-list')
        response = self.client.get(url)
        print(response.data)
        self.assertEqual(response.status_code, 200)  # 127.0.0.1 默认排除
        self.assertEqual(response.data['results'], [])

        self.host1 = get_or_create_host(ipv4='192.168.111.1', pcserver_host_ipv4='192.168.111.1')
        response = self.client.get(url)
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'ipv4', 'group', 'vcpu_total', 'vcpu_allocated', 'mem_total', 'mem_allocated', 'vm_limit',
             'vm_created', 'enable', 'desc', 'mem_unit'], response.data['results'][0])

        self.assertEqual(response.data['results'][0]['mem_unit'], 'MB')
        self.assertEqual(response.data['results'][0]['mem_total'], self.host.mem_total * 1024)
        self.assertEqual(response.data['results'][0]['mem_allocated'], self.host.mem_allocated * 1024)

        query = parse.urlencode(query={'mem_unit': 'GB'})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'ipv4', 'group', 'vcpu_total', 'vcpu_allocated', 'mem_total', 'mem_allocated', 'vm_limit',
             'vm_created', 'enable', 'desc', 'mem_unit'], response.data['results'][0])

        self.assertEqual(response.data['results'][0]['mem_unit'], 'GB')
        self.assertEqual(response.data['results'][0]['mem_total'], self.host.mem_total)
        self.assertEqual(response.data['results'][0]['mem_allocated'], self.host.mem_allocated)

        query = parse.urlencode(query={'mem_unit': 'MB'})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'ipv4', 'group', 'vcpu_total', 'vcpu_allocated', 'mem_total', 'mem_allocated', 'vm_limit',
             'vm_created', 'enable', 'desc', 'mem_unit'], response.data['results'][0])

        self.assertEqual(response.data['results'][0]['mem_unit'], 'MB')
        self.assertEqual(response.data['results'][0]['mem_total'], self.host.mem_total * 1024)
        self.assertEqual(response.data['results'][0]['mem_allocated'], self.host.mem_allocated * 1024)

        query = parse.urlencode(query={'mem_unit': 'KB'})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['err_code'], 'BadRequest')

        # 宿主机组
        query = parse.urlencode(query={'group_id': self.host.group_id})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'ipv4', 'group', 'vcpu_total', 'vcpu_allocated', 'mem_total', 'mem_allocated', 'vm_limit',
             'vm_created', 'enable', 'desc', 'mem_unit'], response.data['results'][0])

        self.assertEqual(response.data['results'][0]['mem_unit'], 'MB')
        self.assertEqual(response.data['results'][0]['mem_total'], self.host.mem_total * 1024)
        self.assertEqual(response.data['results'][0]['mem_allocated'], self.host.mem_allocated * 1024)

        self.host1.delete()

        query = parse.urlencode(query={'mem_unit': 'MB', 'group_id': self.host.group_id})  # 127.0.0.1 主机
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], [])

        self.host1 = get_or_create_host(ipv4='192.168.111.1', pcserver_host_ipv4='192.168.111.1')
        query = parse.urlencode(query={'mem_unit': 'MB', 'group_id': self.host1.group_id})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'ipv4', 'group', 'vcpu_total', 'vcpu_allocated', 'mem_total', 'mem_allocated', 'vm_limit',
             'vm_created', 'enable', 'desc', 'mem_unit'], response.data['results'][0])

        self.assertEqual(response.data['results'][0]['mem_unit'], 'MB')
        self.assertEqual(response.data['results'][0]['mem_total'], self.host1.mem_total * 1024)
        self.assertEqual(response.data['results'][0]['mem_allocated'], self.host1.mem_allocated * 1024)

        query = parse.urlencode(query={'mem_unit': 'GB', 'group_id': self.host1.group_id})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'ipv4', 'group', 'vcpu_total', 'vcpu_allocated', 'mem_total', 'mem_allocated', 'vm_limit',
             'vm_created', 'enable', 'desc', 'mem_unit'], response.data['results'][0])

        self.assertEqual(response.data['results'][0]['mem_unit'], 'GB')
        self.assertEqual(response.data['results'][0]['mem_total'], self.host1.mem_total)
        self.assertEqual(response.data['results'][0]['mem_allocated'], self.host1.mem_allocated)

        query = parse.urlencode(query={'group_id': 100})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], [])

        query = parse.urlencode(query={'group_id': -1})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['err_code'], 'BadRequest')
