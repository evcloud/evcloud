from urllib import parse
from django.urls import reverse
from . import MyAPITestCase, get_or_create_user, get_or_create_host


class computequotaTests(MyAPITestCase):
    """可用总资源配额和已用配额信息测试"""

    def setUp(self) -> None:
        self.user = get_or_create_user()
        self.host = get_or_create_host()

    def test_list_compute_quota(self):
        self.client.force_login(self.user)
        url = reverse('api:compute-quota-list')

        response = self.client.get(url)
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['mem_total', 'mem_allocated', 'vcpu_total', 'vcpu_allocated', 'real_cpu', 'vm_created', 'vm_limit',
             'ips_total', 'ips_used', 'mem_unit'], response.data['quota'])

        query = parse.urlencode(query={'mem_unit': 'GB'})  # mem_unit=GB
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['mem_total', 'mem_allocated', 'vcpu_total', 'vcpu_allocated', 'real_cpu', 'vm_created', 'vm_limit',
             'ips_total', 'ips_used', 'mem_unit'], response.data['quota'])

        query = parse.urlencode(query={'mem_unit': 'KB'})  # mem_unit=GB
        response = self.client.get(f'{url}?{query}')
        print(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['err_code'], 'BadRequest')


