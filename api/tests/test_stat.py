from urllib import parse
from django.urls import reverse
from . import MyAPITestCase, get_or_create_user, get_or_create_host, get_or_create_center, get_or_create_group


class statTests(MyAPITestCase):
    """资源统计 测试"""

    def setUp(self) -> None:
        self.user = get_or_create_user()
        self.host = get_or_create_host()

    def test_list_stat(self):
        self.client.force_login(self.user)
        url = reverse('api:stat-list')
        response = self.client.get(url)
        print(response.data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['err_code'], 'permission_denied')

        self.client.logout()
        self.user.is_superuser = True
        self.user.save(update_fields=['is_superuser'])
        self.client.force_login(self.user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'mem_total', 'mem_allocated', 'vcpu_total', 'vcpu_allocated', 'vm_created', 'mem_unit'],
            response.data['centers'][0])
        self.assertEqual(response.data['centers'][0]['mem_unit'], 'MB')

        self.assertKeysIn(
            ['id', 'name', 'center__name', 'mem_total', 'mem_allocated', 'vcpu_total', 'vcpu_allocated', 'vm_created',
             'mem_unit'],
            response.data['groups'][0])
        self.assertEqual(response.data['groups'][0]['mem_unit'], 'MB')

        self.assertKeysIn(
            ['id', 'ipv4', 'group__name', 'mem_total', 'mem_allocated', 'vcpu_total', 'vcpu_allocated', 'vm_created',
             'mem_unit'],
            response.data['hosts'][0])
        self.assertEqual(response.data['hosts'][0]['mem_unit'], 'MB')

        query = parse.urlencode(query={'mem_unit': 'GB'})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'mem_total', 'mem_allocated', 'vcpu_total', 'vcpu_allocated', 'vm_created', 'mem_unit'],
            response.data['centers'][0])
        self.assertEqual(response.data['centers'][0]['mem_unit'], 'GB')

        self.assertKeysIn(
            ['id', 'name', 'center__name', 'mem_total', 'mem_allocated', 'vcpu_total', 'vcpu_allocated', 'vm_created',
             'mem_unit'],
            response.data['groups'][0])
        self.assertEqual(response.data['groups'][0]['mem_unit'], 'GB')

        self.assertKeysIn(
            ['id', 'ipv4', 'group__name', 'mem_total', 'mem_allocated', 'vcpu_total', 'vcpu_allocated', 'vm_created',
             'mem_unit'],
            response.data['hosts'][0])
        self.assertEqual(response.data['hosts'][0]['mem_unit'], 'GB')

    def test_list_stat_center(self):
        """数据中心资源信息统计"""
        self.user.is_superuser = True
        self.user.save(update_fields=['is_superuser'])
        self.client.force_login(self.user)

        url = reverse('api:stat-center-stat', kwargs={'id': self.host.group.center_id})
        response = self.client.get(url)
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'mem_total', 'mem_allocated', 'vcpu_total', 'vcpu_allocated', 'vm_created', 'mem_unit'],
            response.data['center'])
        self.assertEqual(response.data['center']['mem_unit'], 'MB')

        self.assertKeysIn(
            ['id', 'name', 'center__name', 'mem_total', 'mem_allocated', 'vcpu_total', 'vcpu_allocated', 'vm_created',
             'mem_unit'],
            response.data['groups'][0])
        self.assertEqual(response.data['groups'][0]['mem_unit'], 'MB')

        query = parse.urlencode(query={'mem_unit': 'GB'})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'mem_total', 'mem_allocated', 'vcpu_total', 'vcpu_allocated', 'vm_created', 'mem_unit'],
            response.data['center'])
        self.assertEqual(response.data['center']['mem_unit'], 'GB')

        self.assertKeysIn(
            ['id', 'name', 'center__name', 'mem_total', 'mem_allocated', 'vcpu_total', 'vcpu_allocated', 'vm_created',
             'mem_unit'],
            response.data['groups'][0])
        self.assertEqual(response.data['groups'][0]['mem_unit'], 'GB')

    def test_list_stat_group(self):
        """组资源信息统计"""
        self.user.is_superuser = True
        self.user.save(update_fields=['is_superuser'])
        self.client.force_login(self.user)

        url = reverse('api:stat-group-stat', kwargs={'id': self.host.group_id})
        response = self.client.get(url)
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'center__name', 'mem_total', 'mem_allocated', 'vcpu_total', 'vcpu_allocated', 'vm_created',
             'mem_unit'],
            response.data['group'])
        self.assertEqual(response.data['group']['mem_unit'], 'MB')

        self.assertKeysIn(
            ['id', 'ipv4', 'group__name', 'mem_total', 'mem_allocated', 'vcpu_total', 'vcpu_allocated', 'vm_created',
             'mem_unit'],
            response.data['hosts'][0])
        self.assertEqual(response.data['hosts'][0]['mem_unit'], 'MB')

        query = parse.urlencode(query={'mem_unit': 'GB'})
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'center__name', 'mem_total', 'mem_allocated', 'vcpu_total', 'vcpu_allocated', 'vm_created',
             'mem_unit'],
            response.data['group'])
        self.assertEqual(response.data['group']['mem_unit'], 'GB')

        self.assertKeysIn(
            ['id', 'ipv4', 'group__name', 'mem_total', 'mem_allocated', 'vcpu_total', 'vcpu_allocated', 'vm_created',
             'mem_unit'],
            response.data['hosts'][0])
        self.assertEqual(response.data['hosts'][0]['mem_unit'], 'GB')