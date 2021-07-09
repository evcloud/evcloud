from django.test import TestCase

from utils.ev_libvirt.virt import VmDomain, VirtHost


class TestVm(TestCase):
    def test_vm_stats(self):
        # domain = VmDomain(host_ip='10.0.200.83', vm_uuid='4f539a12af494d48882ae4454c505207')
        # try:
        #     stats = domain.get_stats()
        #     print(stats.to_dict())
        # except Exception as e:
        #     pass

        virt_host = VirtHost(host_ipv4='10.0.200.83')
        r = virt_host.get_max_vcpus()
        print(f'max vcpus: {r}')
        r = virt_host.get_defined_domain_num()
        print(f'defined_domain_num: {r}')
