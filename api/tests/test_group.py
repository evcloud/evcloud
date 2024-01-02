from urllib import parse
from django.urls import reverse
from . import MyAPITestCase, get_or_create_user, get_or_create_group, get_or_create_center


class groupTests(MyAPITestCase):
    """宿主机组列表 测试"""

    def setUp(self) -> None:
        self.user = get_or_create_user()
        self.group = get_or_create_group()

    def test_list_group(self):

        self.client.force_login(self.user)
        url = reverse('api:group-list')
        response = self.client.get(url)
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'center', 'desc'], response.data['results'][0])

        query = parse.urlencode(query={'center_id': self.group.center_id})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'center', 'desc'], response.data['results'][0])

        query = parse.urlencode(query={'center_id': 22})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], [])

        # self.group2 = get_or_create_group(name='test_group2', center_name='test_center2')
        self.center = get_or_create_center(name='test_center2')

        query = parse.urlencode(query={'center_id': self.center.id})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], [])

        query = parse.urlencode(query={'center_id': -1})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['err_code'], 'BadRequest')




