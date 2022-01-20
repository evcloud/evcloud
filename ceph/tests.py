import logging

from django.test import TestCase

from .managers import RbdManager


CONF_FILE = '/home/uwsgi/evcloud/data/ceph/conf/2.conf'
KEYRING_FILE = '/home/uwsgi/evcloud/data/ceph/conf/2.keyring'
POOL_NAME = 'vm'
DATA_POOL_NAME = None


class RbdManagerTestCase(TestCase):
    def setUp(self):
        self.pool_name = POOL_NAME
        self.data_pool_name = DATA_POOL_NAME
        self.image_name = 'test_image'
        self.image_rename = 'test_image_rename'
        self.mgr = RbdManager(conf_file=CONF_FILE, keyring_file=KEYRING_FILE, pool_name=self.pool_name)

    def test_image_exists(self):
        image_size = 10 * 1024 ** 2
        ok = self.mgr.create_image(self.image_name, size=image_size, data_pool=self.data_pool_name)
        self.assertIn(ok, [True, None], msg='[Failed] create_image')

        ok = self.mgr.image_exists(self.image_name)
        self.assertTrue(ok, msg='[Failed] image_exists')

        si = self.mgr.get_rbd_image_size(self.image_name)
        self.assertEqual(si, image_size, msg='[Failed] get_rbd_image_size')

        # expand ok
        ok = self.mgr.resize_rbd_image(self.image_name, size=image_size + 1)
        self.assertTrue(ok, msg='[Failed] resize_rbd_image')
        si = self.mgr.get_rbd_image_size(self.image_name)
        self.assertEqual(si, image_size + 1, msg='[Failed] get_rbd_image_size')

        # not allow shrink
        ok = self.mgr.resize_rbd_image(self.image_name, size=image_size)
        self.assertIsNone(ok, msg='[Failed] resize_rbd_image')
        si = self.mgr.get_rbd_image_size(self.image_name)
        self.assertEqual(si, image_size + 1, msg='[Failed] get_rbd_image_size')

        # allow shrink
        ok = self.mgr.resize_rbd_image(self.image_name, size=image_size, allow_shrink=True)
        self.assertTrue(ok, msg='[Failed] resize_rbd_image')
        si = self.mgr.get_rbd_image_size(self.image_name)
        self.assertEqual(si, image_size, msg='[Failed] get_rbd_image_size')

        ok = self.mgr.rename_image(self.image_name, new_name=self.image_rename)
        self.assertTrue(ok, msg='[Failed] rename_image')

        ok = self.mgr.remove_image(self.image_rename)
        self.assertTrue(ok, msg='[Failed] remove_image')

        ok = self.mgr.image_exists(self.image_name)
        self.assertFalse(ok, msg='[Failed] image_exists')

    def tearDown(self):
        self.mgr.remove_image(self.image_name)
        self.mgr.remove_image(self.image_rename)
