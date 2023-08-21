from urllib import parse
from django.urls import reverse
from . import MyAPITestCase, get_or_create_user, get_or_create_flavor


class flavorTests(MyAPITestCase):
    """硬件配置样式 测试"""

    def setUp(self) -> None:
        self.user = get_or_create_user()
        self.flavor = get_or_create_flavor()

    def test_list_flavor(self):
        self.client.force_login(self.user)
        url = reverse('api:flavor-list')

        response = self.client.get(url)
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'vcpus', 'ram', 'mem_unit'], response.data['results'][0])

        self.assertEqual(response.data['results'][0]['ram'], self.flavor.ram * 1024)

        query = parse.urlencode(query={'mem_unit': 'GB'})  # mem_unit=GB
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'vcpus', 'ram', 'mem_unit'], response.data['results'][0])

        self.assertEqual(response.data['results'][0]['ram'], self.flavor.ram)

        query = parse.urlencode(query={'mem_unit': 'KB'})  # mem_unit=GB
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['err_code'], 'BadRequest')
