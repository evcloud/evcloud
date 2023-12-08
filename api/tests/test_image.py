from urllib import parse
from django.urls import reverse
from . import MyAPITestCase, get_or_create_user, get_or_create_center, get_or_create_image


class imageTests(MyAPITestCase):

    def setUp(self) -> None:
        self.user = get_or_create_user()
        self.image = get_or_create_image(user=self.user)

    def test_list_image(self):
        url = reverse('api:image-list')
        response = self.client.get(url)
        # 未登录
        # --------------------------------------------- 未登录 ( not login )-----------------------------------------
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['err_code'], 'NotAuthenticated')

        # --------------------------------------------- 登录 ( login )---------------------------------------------------
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'tag', 'sys_type', 'release', 'version', 'architecture', 'enable', 'create_time',
             'desc', 'default_user', 'default_password', 'size'], response.data['results'][0])

        self.assertKeysIn(['id', 'name'], response.data['results'][0]['tag'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['sys_type'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['release'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['architecture'])

        # --------------------------------------------- 条件过滤 ( conditional filtering )--------------------------------
        # query 参数： center_id
        center = get_or_create_center()
        query = parse.urlencode(query={'center_id': center.id})
        response = self.client.get(f'{url}?{query}')
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'tag', 'sys_type', 'release', 'version', 'architecture', 'enable', 'create_time',
             'desc', 'default_user', 'default_password', 'size'], response.data['results'][0])

        self.assertKeysIn(['id', 'name'], response.data['results'][0]['tag'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['sys_type'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['release'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['architecture'])

        # tag : 1 基础镜像 2 用户镜像
        query = parse.urlencode(query={'tag': 1})
        response = self.client.get(f'{url}?{query}')
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn([], response.data['results'])

        query = parse.urlencode(query={'tag': 2})
        response = self.client.get(f'{url}?{query}')
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'tag', 'sys_type', 'release', 'version', 'architecture', 'enable', 'create_time',
             'desc', 'default_user', 'default_password', 'size'], response.data['results'][0])

        self.assertKeysIn(['id', 'name'], response.data['results'][0]['tag'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['sys_type'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['release'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['architecture'])

        # sys_type 系统类型
        query = parse.urlencode(query={'sys_type': 2})
        response = self.client.get(f'{url}?{query}')
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'tag', 'sys_type', 'release', 'version', 'architecture', 'enable', 'create_time',
             'desc', 'default_user', 'default_password', 'size'], response.data['results'][0])

        self.assertKeysIn(['id', 'name'], response.data['results'][0]['tag'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['sys_type'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['release'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['architecture'])

        query = parse.urlencode(query={'sys_type': 6})
        response = self.client.get(f'{url}?{query}')
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn([], response.data['results'])

        # search ： name 名称 desc 描述
        query = parse.urlencode(query={'search': 'test_image'})
        response = self.client.get(f'{url}?{query}')
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'tag', 'sys_type', 'release', 'version', 'architecture', 'enable', 'create_time',
             'desc', 'default_user', 'default_password', 'size'], response.data['results'][0])

        self.assertKeysIn(['id', 'name'], response.data['results'][0]['tag'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['sys_type'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['release'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['architecture'])

        query = parse.urlencode(query={'search': 'centos9'})
        response = self.client.get(f'{url}?{query}')
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn([], response.data['results'])

        query = parse.urlencode(query={'search': '系统镜像测试'})
        response = self.client.get(f'{url}?{query}')
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'tag', 'sys_type', 'release', 'version', 'architecture', 'enable', 'create_time',
             'desc', 'default_user', 'default_password', 'size'], response.data['results'][0])

        self.assertKeysIn(['id', 'name'], response.data['results'][0]['tag'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['sys_type'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['release'])
        self.assertKeysIn(['id', 'name'], response.data['results'][0]['architecture'])

        query = parse.urlencode(query={'search': '系统镜像测试1'})
        response = self.client.get(f'{url}?{query}')
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn([], response.data['results'])

    def test_detail_image(self):
        self.client.force_login(self.user)
        url = reverse('api:image-detail', kwargs={'id': self.image.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn(
            ['id', 'name', 'tag', 'sys_type', 'release', 'version', 'architecture', 'enable', 'create_time',
             'desc', 'default_user', 'default_password', 'size'], response.data)

        self.assertKeysIn(['id', 'name'], response.data['tag'])
        self.assertKeysIn(['id', 'name'], response.data['sys_type'])
        self.assertKeysIn(['id', 'name'], response.data['release'])
        self.assertKeysIn(['id', 'name'], response.data['architecture'])

        url = reverse('api:image-detail', kwargs={'id': 11})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['err_code'], 'NoSuchImage')

        url = reverse('api:image-detail', kwargs={'id': 'test'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['err_code'], 'BadRequest')

    def test_vm_remark_image(self):
        self.client.force_login(self.user)
        url = reverse('api:image-image-remark', kwargs={'id': self.image.id})
        query = parse.urlencode(query={'remark': '修改济镜像备注'})
        response = self.client.patch(f'{url}?{query}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code_text'], '修改虚拟机备注信息成功')

        url = reverse('api:image-image-remark', kwargs={'id': 11})
        query = parse.urlencode(query={'remark': '修改济镜像备注'})
        response = self.client.patch(f'{url}?{query}')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['err_code'], 'BadRequest')
        url = reverse('api:image-image-remark', kwargs={'id': '"' + str(self.image.id) + '"'})
        query = parse.urlencode(query={'remark': '修改济镜像备注'})

        response = self.client.patch(f'{url}?{query}')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['err_code'], 'BadRequest')
