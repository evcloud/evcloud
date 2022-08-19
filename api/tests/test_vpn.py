from urllib import parse

from django.urls import reverse

from vpn.models import VPNAuth
from . import MyAPITestCase, get_or_create_user


class PaymentHistoryTests(MyAPITestCase):
    def setUp(self):
        self.user = get_or_create_user()

    def test_vpn(self):
        vpn_username = 'testvpn'

        self.client.force_login(self.user)

        # create vpn
        base_url = reverse('api:vpn-list')
        r = self.client.post(base_url, data={'username': vpn_username, 'password': 'vpnpassword'})
        self.assertEqual(r.status_code, 201)
        self.assertKeysIn(["username", "password", "active", "create_time", "modified_time"], r.data)
        self.assert_is_subdict_of(sub={'username': vpn_username, 'password': 'vpnpassword', 'active': False}, d=r.data)

        # get vpn
        detail_url = reverse('api:vpn-detail', kwargs={'username': vpn_username})
        r = self.client.get(detail_url)
        self.assertEqual(r.status_code, 200)
        self.assertKeysIn(["username", "password", "active", "create_time", "modified_time"], r.data)
        self.assert_is_subdict_of(sub={'username': 'testvpn', 'password': 'vpnpassword', 'active': False}, d=r.data)

        # change password
        query = parse.urlencode(query={'password': 'new_password'})
        r = self.client.patch(f'{detail_url}?{query}')
        self.assertEqual(r.status_code, 200)
        self.assertKeysIn(["username", "password", "active", "create_time", "modified_time"], r.data)
        self.assert_is_subdict_of(sub={'username': 'testvpn', 'password': 'new_password', 'active': False}, d=r.data)

        vpn = VPNAuth.objects.filter(username=vpn_username).first()
        self.assertEqual(vpn.password, "new_password")
        vpn.active = False
        vpn.save(update_fields=['active'])

        # active
        active_url = reverse('api:vpn-active-vpn', kwargs={'username': vpn_username})
        r = self.client.post(active_url)
        self.assertEqual(r.status_code, 200)
        self.assertKeysIn(["username", "password", "active", "create_time", "modified_time"], r.data)
        self.assert_is_subdict_of(sub={'username': 'testvpn', 'password': 'new_password', 'active': True}, d=r.data)
        vpn.refresh_from_db()
        self.assertIs(vpn.active, True)

        # deactive
        deactive_url = reverse('api:vpn-deactive-vpn', kwargs={'username': vpn_username})
        r = self.client.post(deactive_url)
        self.assertEqual(r.status_code, 200)
        self.assertKeysIn(["username", "password", "active", "create_time", "modified_time"], r.data)
        self.assert_is_subdict_of(sub={'username': 'testvpn', 'password': 'new_password', 'active': False}, d=r.data)
        vpn.refresh_from_db()
        self.assertIs(vpn.active, False)
