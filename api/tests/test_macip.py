from urllib import parse

from django.urls import reverse
from . import MyAPITestCase, get_or_create_user, get_or_create_macip, get_or_create_vlan


class macipTests(MyAPITestCase):
    """宿主机组列表 测试"""

    def setUp(self) -> None:
        self.user = get_or_create_user()
        # 默认 test_br
        self.macip = get_or_create_macip(ipv4='192.168.1.2')
        self.macip_used = get_or_create_macip(ipv4='192.168.1.3', used=True, mac='DA:59:68:42:7D:3B')
        self.vlan1 = get_or_create_vlan()  # 默认
        # test_br2
        self.vlan2 = get_or_create_vlan(br='test_br2', tag=1)  # 公网
        self.macip_used2 = get_or_create_macip(ipv4='192.168.1.4', used=True, mac='AE:DE:8B:8D:44:4B', vlan=self.vlan2)
        self.macip2 = get_or_create_macip(ipv4='192.168.1.5', mac='5A:73:B5:7F:85:4F', vlan=self.vlan2)

    def test_list_macip(self):
        self.client.force_login(self.user)
        url = reverse('api:macip-list')
        response = self.client.get(url)
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'mac', 'ipv4', 'ipv6', 'used'], response.data['results'][0])

        # 查询 被占用 ip
        query = parse.urlencode(query={'used': 'true'})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'mac', 'ipv4', 'ipv6', 'used'], response.data['results'][0])
        self.assertEqual(response.data['results'][0]['used'], True)

        # 查询 未占用的 ip
        query = parse.urlencode(query={'used': 'false'})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'mac', 'ipv4', 'ipv6', 'used'], response.data['results'][0])
        self.assertEqual(response.data['results'][0]['used'], False)

        # 根据vlan_id 查询
        query = parse.urlencode(query={'vlan_id': self.vlan1.id})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'mac', 'ipv4', 'ipv6', 'used'], response.data['results'][0])

        # 不存在的vlan
        query = parse.urlencode(query={'vlan_id': 10})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], [])

        query = parse.urlencode(query={'vlan_id': self.vlan1.id, 'used': 'false'})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'mac', 'ipv4', 'ipv6', 'used'], response.data['results'][0])

        self.assertEqual(response.data['results'][0]['used'], False)
        self.assertEqual(response.data['results'][0]['ipv4'], '192.168.1.2')

        query = parse.urlencode(query={'vlan_id': self.vlan1.id, 'used': 'true'})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'mac', 'ipv4', 'ipv6', 'used'], response.data['results'][0])

        self.assertEqual(response.data['results'][0]['used'], True)
        self.assertEqual(response.data['results'][0]['ipv4'], '192.168.1.3')

        query = parse.urlencode(query={'vlan_id': self.vlan2.id, 'used': 'true'})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'mac', 'ipv4', 'ipv6', 'used'], response.data['results'][0])

        self.assertEqual(response.data['results'][0]['used'], True)
        self.assertEqual(response.data['results'][0]['ipv4'], '192.168.1.4')

        query = parse.urlencode(query={'vlan_id': self.vlan2.id, 'used': 'false'})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'mac', 'ipv4', 'ipv6', 'used'], response.data['results'][0])

        self.assertEqual(response.data['results'][0]['used'], False)
        self.assertEqual(response.data['results'][0]['ipv4'], '192.168.1.5')
