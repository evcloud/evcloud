from django.urls import reverse

from api.tests import MyAPITestCase, get_or_create_user

from vms.models import VmSharedUser
from users.models import UserProfile
from . import config_res_admin, create_vm_metadata


class VmSharedUserTests(MyAPITestCase):
    def setUp(self):
        self.res_user = get_or_create_user(username='resuser1@cnic.cn')

    def test_replace(self):
        user1 = get_or_create_user(username='user1@qq.com')
        vm1 = create_vm_metadata(uuid='test-vm-uuid1', owner=self.res_user)
        vm2 = create_vm_metadata(uuid='test-vm-uuid2', owner=user1)

        # vm2 shared user
        VmSharedUser(
            vm=vm2, user=self.res_user, permission=VmSharedUser.Permission.READONLY.value
        ).save(force_insert=True)

        self.client.force_login(self.res_user)
        self.assertEqual(UserProfile.objects.count(), 2)
        self.assertEqual(VmSharedUser.objects.count(), 1)
        url = reverse('api:share-vm-user-replace', kwargs={'vm_id': 'test'})
        response = self.client.post(url, data={
            'users': [
                {'username': 'user1@qq.com', 'role': VmSharedUser.Permission.READWRITE.value}
            ]
        })
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['err_code'], 'VmNotExist')

        url = reverse('api:share-vm-user-replace', kwargs={'vm_id': vm1.uuid})
        response = self.client.post(url, data={
            'users': [
                {'username': 'user1@qq.com', 'role': VmSharedUser.Permission.READWRITE.value}
            ]
        })
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['err_code'], 'VmAccessDenied')

        # 资源管理员
        config_res_admin(username=self.res_user.username, is_res=True)
        # ok
        response = self.client.post(url, data={
            'users': [
                {'username': 'user1@qq.com', 'role': VmSharedUser.Permission.READWRITE.value}
            ]
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(UserProfile.objects.count(), 2)
        self.assertEqual(VmSharedUser.objects.count(), 2)

        # required users
        response = self.client.post(url, data={
            'user': [
                {'username': 'user1@qq.com', 'role': VmSharedUser.Permission.READONLY.value}
            ]
        })
        self.assertEqual(response.status_code, 400)

        # invalid username
        response = self.client.post(url, data={
            'user': [
                {'username': 'use#@qq.com', 'role': VmSharedUser.Permission.READONLY.value}
            ]
        })
        self.assertEqual(response.status_code, 400)

        self.assertEqual(UserProfile.objects.count(), 2)
        self.assertEqual(VmSharedUser.objects.count(), 2)

        # 移除所有共享用户
        response = self.client.post(url, data={
            'users': []
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(UserProfile.objects.count(), 2)
        self.assertEqual(VmSharedUser.objects.count(), 1)

        # invalid roles
        response = self.client.post(url, data={
            'users': [
                {'username': 'user1@qq.com', 'roles': VmSharedUser.Permission.READONLY.value}
            ]
        })
        self.assertEqual(response.status_code, 400)

        # ok
        self.assertEqual(UserProfile.objects.count(), 2)
        self.assertEqual(VmSharedUser.objects.count(), 1)
        response = self.client.post(url, data={
            'users': [
                {'username': 'user1@qq.com', 'role': VmSharedUser.Permission.READONLY.value},
                {'username': 'user2@qq.com', 'role': VmSharedUser.Permission.READWRITE.value},
                {'username': 'user3@qq.com', 'role': VmSharedUser.Permission.READONLY.value}
            ]
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(UserProfile.objects.count(), 4)
        self.assertEqual(VmSharedUser.objects.count(), 4)
        self.assertEqual(VmSharedUser.objects.filter(vm_id=vm1.uuid).count(), 3)
        vm1_sh_user_dict = {
            sh_u.user.username: sh_u for sh_u in VmSharedUser.objects.select_related('user').filter(vm_id=vm1.uuid)}
        self.assertEqual(vm1_sh_user_dict['user1@qq.com'].permission, VmSharedUser.Permission.READONLY.value)
        self.assertEqual(vm1_sh_user_dict['user2@qq.com'].permission, VmSharedUser.Permission.READWRITE.value)
        self.assertEqual(vm1_sh_user_dict['user3@qq.com'].permission, VmSharedUser.Permission.READONLY.value)

        # remove user1, change user2, add user4
        response = self.client.post(url, data={
            'users': [
                {'username': 'user2@qq.com', 'role': VmSharedUser.Permission.READONLY.value},
                {'username': 'user3@qq.com', 'role': VmSharedUser.Permission.READONLY.value},
                {'username': 'user4@qq.com', 'role': VmSharedUser.Permission.READWRITE.value}
            ]
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(UserProfile.objects.count(), 5)
        self.assertEqual(VmSharedUser.objects.count(), 4)
        self.assertEqual(VmSharedUser.objects.filter(vm_id=vm1.uuid).count(), 3)
        vm1_sh_user_dict = {
            sh_u.user.username: sh_u for sh_u in VmSharedUser.objects.select_related('user').filter(vm_id=vm1.uuid)}
        self.assertEqual(vm1_sh_user_dict['user2@qq.com'].permission, VmSharedUser.Permission.READONLY.value)
        self.assertEqual(vm1_sh_user_dict['user3@qq.com'].permission, VmSharedUser.Permission.READONLY.value)
        self.assertEqual(vm1_sh_user_dict['user4@qq.com'].permission, VmSharedUser.Permission.READWRITE.value)

        # remove user2/3, change user4
        response = self.client.post(url, data={
            'users': [
                {'username': 'user4@qq.com', 'role': VmSharedUser.Permission.READONLY.value}
            ]
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(UserProfile.objects.count(), 5)
        self.assertEqual(VmSharedUser.objects.count(), 2)
        self.assertEqual(VmSharedUser.objects.filter(vm_id=vm1.uuid).count(), 1)
        vm1_sh_user_dict = {
            sh_u.user.username: sh_u for sh_u in VmSharedUser.objects.select_related('user').filter(vm_id=vm1.uuid)}
        self.assertEqual(vm1_sh_user_dict['user4@qq.com'].permission, VmSharedUser.Permission.READONLY.value)

    def test_list(self):
        user1 = get_or_create_user(username='user1@qq.com')
        user2 = get_or_create_user(username='user2@qq.com')
        vm1 = create_vm_metadata(uuid='test-vm-uuid1', owner=self.res_user)
        vm2 = create_vm_metadata(uuid='test-vm-uuid2', owner=user1)

        # vm1 shared user
        VmSharedUser(
            vm=vm1, user=user1, permission=VmSharedUser.Permission.READONLY.value
        ).save(force_insert=True)

        VmSharedUser(
            vm=vm1, user=user2, permission=VmSharedUser.Permission.READWRITE.value
        ).save(force_insert=True)

        # vm2 shared user
        VmSharedUser(
            vm=vm2, user=self.res_user, permission=VmSharedUser.Permission.READONLY.value
        ).save(force_insert=True)

        self.client.force_login(self.res_user)
        url = reverse('api:share-vm-user-list', kwargs={'vm_id': 'test'})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['err_code'], 'VmNotExist')

        url = reverse('api:share-vm-user-list', kwargs={'vm_id': vm1.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['err_code'], 'VmAccessDenied')

        # 资源管理员
        config_res_admin(username=self.res_user.username, is_res=True)
        # ok
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['shared_users']), 2)
        sh_user_dict = {sh_u['user']['username']: sh_u for sh_u in response.data['shared_users']}
        self.assertEqual(sh_user_dict[user1.username]['permission'], VmSharedUser.Permission.READONLY.value)
        self.assertEqual(sh_user_dict[user2.username]['permission'], VmSharedUser.Permission.READWRITE.value)

        # 移除资源管理员
        config_res_admin(username=self.res_user.username, is_res=False)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['err_code'], 'VmAccessDenied')

        # superuser ok
        self.res_user.is_superuser = True
        self.res_user.save(update_fields=['is_superuser'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['shared_users']), 2)
        sh_user_dict = {sh_u['user']['username']: sh_u for sh_u in response.data['shared_users']}
        self.assertEqual(sh_user_dict[user1.username]['permission'], VmSharedUser.Permission.READONLY.value)
        self.assertEqual(sh_user_dict[user2.username]['permission'], VmSharedUser.Permission.READWRITE.value)
