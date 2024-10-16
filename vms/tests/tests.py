from django.test import TestCase

from utils.ev_libvirt.virt import VmDomain, VirtHost
from vms.xml import XMLEditor
from vms.xml_builder import VmXMLBuilder

xml_tpl = """
<domain type="kvm">
  <name>win10</name>
  <cpu mode="host-passthrough" check="none" migratable="on"/>
</domain>
"""


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


class TestXML(TestCase):

    def setUp(self):
        self.vm_xml_builder = VmXMLBuilder()
        self.max_cpu_sockets = 2

    def test_add_cpu_topology_cores(self):
        core_num = self.vm_xml_builder.get_cpu_topology_cores(vcpu=10, max_cpu_sockets=1)
        self.assertEqual(core_num, 10)

        core_num = self.vm_xml_builder.get_cpu_topology_cores(vcpu=1, max_cpu_sockets=2)
        self.assertEqual(core_num, None)

        core_num = self.vm_xml_builder.get_cpu_topology_cores(vcpu=10, max_cpu_sockets=2)
        self.assertEqual(core_num, 5)

        core_num = self.vm_xml_builder.get_cpu_topology_cores(vcpu=2, max_cpu_sockets=4)
        self.assertEqual(core_num, None)

        core_num = self.vm_xml_builder.get_cpu_topology_cores(vcpu=7, max_cpu_sockets=2)
        self.assertEqual(core_num, None)

        core_num = self.vm_xml_builder.get_cpu_topology_cores(vcpu="1", max_cpu_sockets="1")
        self.assertEqual(core_num, None)

        core_num = self.vm_xml_builder.get_cpu_topology_cores(vcpu="1", max_cpu_sockets=1)
        self.assertEqual(core_num, None)

        core_num = self.vm_xml_builder.get_cpu_topology_cores(vcpu=1, max_cpu_sockets='1')
        self.assertEqual(core_num, None)

        core_num = self.vm_xml_builder.get_cpu_topology_cores(vcpu="10", max_cpu_sockets="2")
        self.assertEqual(core_num, None)

    def test_xml(self):
        """"""
        self.vm_xml_builder = VmXMLBuilder()
        core_num = self.vm_xml_builder.get_cpu_topology_cores(vcpu=10, max_cpu_sockets=self.max_cpu_sockets)

        xml_desc = self.vm_xml_builder.add_cpu_topology_xml(xml_desc=xml_tpl, max_cpu_sockets=2, cores_num=core_num)

        print(xml_desc)
        core_num = self.vm_xml_builder.get_cpu_topology_cores(vcpu=1, max_cpu_sockets=self.max_cpu_sockets)

        xml_desc = self.vm_xml_builder.add_cpu_topology_xml(xml_desc=xml_tpl, max_cpu_sockets=2, cores_num=core_num)
        print(xml_desc)

        xml_desc = self.vm_xml_builder.add_cpu_topology_xml(xml_desc=xml_tpl, max_cpu_sockets=2, cores_num=1)
        print(xml_desc)
