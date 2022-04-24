from django.urls import reverse

from image.models import Image

from . import MyAPITestCase, get_or_create_user, get_or_create_ceph_pool, get_or_create_xml_temp


class imageTests(MyAPITestCase):
    def setUp(self) -> None:
        self.user = get_or_create_user()
        self.pool = get_or_create_ceph_pool()

    def test_detail_image(self):
        temp = get_or_create_xml_temp()
        image = Image(
            name='镜像名称',
            version='系统版本信息',
            ceph_pool=self.pool,
            tag=Image.TAG_USER,
            sys_type=Image.SYS_TYPE_LINUX,
            base_image='',
            xml_tpl=temp,
            user=self.user,
            size=100
        )
        super(Image, image).save(force_insert=True)

        url = reverse('api:image-detail', kwargs={'id': 'test'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['err_code'], 'NotAuthenticated')

        self.client.force_login(self.user)
        url = reverse('api:image-detail', kwargs={'id': 'test'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['err_code'], 'BadRequest')

        url = reverse('api:image-detail', kwargs={'id': 100})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['err_code'], 'NoSuchImage')

        url = reverse('api:image-detail', kwargs={'id': image.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertKeysIn([
            "id", "name", "version", "sys_type", "tag", "enable", "create_time",
            "desc", "default_user", "default_password", "size"
        ], response.data)
