from django.urls import reverse

from api.tests import MyAPITestCase, get_or_create_user

from vms.models import VmSharedUser
from . import config_res_admin, create_vm_metadata


class VmPermTests(MyAPITestCase):
    def setUp(self):
        self.res_user = get_or_create_user(username='resuser1@cnic.cn')

    def test_vm_action(self):
        user1 = get_or_create_user(username='user1@qq.com')
        vm1 = create_vm_metadata(uuid='test-vm-uuid2', owner=user1)

        # owner user1 can action
        self.client.force_login(user1)
        url = reverse('api:vms-vm-operations', kwargs={'uuid': 'test'})
        response = self.client.patch(url, data={'op': 'start'})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['err_code'], 'VmNotExist')

        url = reverse('api:vms-vm-operations', kwargs={'uuid': vm1.uuid})
        response = self.client.patch(url, data={'op': 'start'})
        self.assertEqual(response.status_code, 500)

        response = self.client.patch(url, data={'op': 'delete'})
        self.assertEqual(response.status_code, 403)

        self.client.logout()
        self.client.force_login(self.res_user)
        response = self.client.patch(url, data={'op': 'start'})
        self.assertEqual(response.status_code, 403)

        # superuser ok
        self.res_user.is_superuser = True
        self.res_user.save(update_fields=['is_superuser'])
        response = self.client.patch(url, data={'op': 'start'})
        self.assertEqual(response.status_code, 500)

        self.res_user.is_superuser = False
        self.res_user.save(update_fields=['is_superuser'])
        response = self.client.patch(url, data={'op': 'start'})
        self.assertEqual(response.status_code, 403)

        # 资源管理员 ok
        config_res_admin(username=self.res_user.username, is_res=True)
        response = self.client.patch(url, data={'op': 'start'})
        self.assertEqual(response.status_code, 500)

        config_res_admin(username=self.res_user.username, is_res=False)
        response = self.client.patch(url, data={'op': 'start'})
        self.assertEqual(response.status_code, 403)

        # 共享用户
        sh_user = VmSharedUser(
            vm=vm1, user=self.res_user, permission=VmSharedUser.Permission.READONLY.value
        )
        sh_user.save(force_insert=True)
        response = self.client.patch(url, data={'op': 'start'})
        self.assertEqual(response.status_code, 403)

        sh_user.permission = VmSharedUser.Permission.READWRITE.value
        sh_user.save(update_fields=['permission'])
        response = self.client.patch(url, data={'op': 'start'})
        self.assertEqual(response.status_code, 500)

        response = self.client.patch(url, data={'op': 'delete'})
        self.assertEqual(response.status_code, 403)
