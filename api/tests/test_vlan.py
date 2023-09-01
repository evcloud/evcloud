from urllib import parse
from django.urls import reverse
from . import MyAPITestCase, get_or_create_user, get_or_create_vlan


class vlanTests(MyAPITestCase):
    """vlan列表 测试"""

    def setUp(self) -> None:
        self.user = get_or_create_user()
        self.user2 = get_or_create_user(username='user2', password='user2')
        self.vlan = get_or_create_vlan()

    def test_list_vlan(self):
        self.client.force_login(self.user)
        url = reverse('api:vlan-list')
        response = self.client.get(url)
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'br', 'tag', 'enable', 'subnet_ip', 'net_mask', 'gateway', 'dns_server', 'subnet_ip_v6',
             'net_mask_v6', 'gateway_v6', 'dns_server_v6', 'remarks'], response.data['results'][0])

        # 参数：center_id
        query = parse.urlencode(query={'center_id': self.vlan.group.center_id})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'br', 'tag', 'enable', 'subnet_ip', 'net_mask', 'gateway', 'dns_server', 'subnet_ip_v6',
             'net_mask_v6', 'gateway_v6', 'dns_server_v6', 'remarks'], response.data['results'][0])

        query = parse.urlencode(query={'center_id': 100})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['err_code'], 'NotFound')

        # 参数：group_id
        query = parse.urlencode(query={'group_id': self.vlan.group_id})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'br', 'tag', 'enable', 'subnet_ip', 'net_mask', 'gateway', 'dns_server', 'subnet_ip_v6',
             'net_mask_v6', 'gateway_v6', 'dns_server_v6', 'remarks'], response.data['results'][0])

        query = parse.urlencode(query={'group_id': 111})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], [])

        # 参数：public
        query = parse.urlencode(query={'public': 'false'})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'br', 'tag', 'enable', 'subnet_ip', 'net_mask', 'gateway', 'dns_server', 'subnet_ip_v6',
             'net_mask_v6', 'gateway_v6', 'dns_server_v6', 'remarks'], response.data['results'][0])

        query = parse.urlencode(query={'public': 'true'})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], [])

        self.vlan.tag = 1  # 公网
        self.vlan.save(update_fields=['tag'])
        query = parse.urlencode(query={'public': 'true'})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'br', 'tag', 'enable', 'subnet_ip', 'net_mask', 'gateway', 'dns_server', 'subnet_ip_v6',
             'net_mask_v6', 'gateway_v6', 'dns_server_v6', 'remarks'], response.data['results'][0])

        self.client.logout()

        # 参数：available
        self.client.force_login(self.user2)
        query = parse.urlencode(query={'available': '123', 'group_id': self.vlan.group_id})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], [])

        self.vlan.group.users.add(self.user2)
        query = parse.urlencode(query={'available': '123', 'group_id': self.vlan.group_id})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'br', 'tag', 'enable', 'subnet_ip', 'net_mask', 'gateway', 'dns_server', 'subnet_ip_v6',
             'net_mask_v6', 'gateway_v6', 'dns_server_v6', 'remarks'], response.data['results'][0])

    def test_list_vlan_id(self):
        self.client.force_login(self.user)
        url = reverse('api:vlan-detail', kwargs={'id': self.vlan.id})
        print(url)
        response = self.client.get(url)
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'br', 'tag', 'enable', 'subnet_ip', 'net_mask', 'gateway', 'dns_server', 'subnet_ip_v6',
             'net_mask_v6', 'gateway_v6', 'dns_server_v6', 'remarks'], response.data)

        url = reverse('api:vlan-detail', kwargs={'id': '"' + str(self.vlan.id) + '"'})
        response = self.client.get(url)
        print(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['err_code'], 'BadRequest')

        url = reverse('api:vlan-detail', kwargs={'id': 100})
        response = self.client.get(url)
        print(response.data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['err_code'], 'NotFound')
