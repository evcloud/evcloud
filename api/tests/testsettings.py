TEST_HOST = '127.0.0.1' #'192.168.50.11'
TEST_HOST_2 = '127.0.0.1'
TEST_CEPH = {'host': '127.0.0.1',#'192.168.50.11',
             'pool': 'vm',
             'port': 6789,
             'uuid': 'b1b874e4-ab2f-427b-9393-33be24fa7810'}
TEST_IMAGE = '0000_demo_winxp@20180629'
TEST_VLAN = '10.10.20.0'
TEST_BR = 'br_local'
TEST_MAC = 'C8:00:A0:A0:B0:77'
TEST_IP = '10.10.20.119'
TEST_XML = '''
<domain type='kvm'>
  <name>%(name)s</name>
  <uuid>%(uuid)s</uuid>
  <memory unit='MiB'>%(mem)d</memory>
  <currentMemory unit='MiB'>%(mem)d</currentMemory>
  <vcpu placement='static'>%(vcpu)d</vcpu>
  <os>
    <type arch='x86_64' machine='pc-i440fx-2.3'>hvm</type>
  </os>
  <features>
    <acpi/>
    <apic/>
    <pae/>
  </features>
<!--   <cpu mode='custom' match='exact'>
    <model fallback='allow'>SandyBridge</model>
  </cpu> -->
  <clock offset='utc'>
    <timer name='rtc' tickpolicy='catchup'/>
    <timer name='pit' tickpolicy='delay'/>
    <timer name='hpet' present='no'/>
  </clock>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>restart</on_crash>
  <pm>
    <suspend-to-mem enabled='no'/>
    <suspend-to-disk enabled='no'/>
  </pm>
  <devices>
    <emulator>/usr/bin/qemu-kvm</emulator>
    <disk type='network' device='disk'>
      <driver name='qemu'/>
      <auth username='admin'>
        <secret type='ceph' uuid='%(ceph_uuid)s'/>
      </auth>
      <source protocol='rbd' name='%(ceph_pool)s/%(diskname)s'>
        <host name='%(ceph_host)s' port='%(ceph_port)s'/>
      </source>
      <target dev='vda' bus='virtio'/>
      <boot order='1'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x07' function='0x0'/>
    </disk>
    <controller type='usb' index='0' model='ich9-ehci1'>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x06' function='0x7'/>
    </controller>
    <controller type='usb' index='0' model='ich9-uhci1'>
      <master startport='0'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x06' function='0x0' multifunction='on'/>
    </controller>
    <controller type='usb' index='0' model='ich9-uhci2'>
      <master startport='2'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x06' function='0x1'/>
    </controller>
    <controller type='usb' index='0' model='ich9-uhci3'>
      <master startport='4'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x06' function='0x2'/>
    </controller>
    <controller type='pci' index='0' model='pci-root'/>
    <controller type='virtio-serial' index='0'>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x05' function='0x0'/>
    </controller>
    <interface type='bridge'>
      <mac address='%(mac)s'/>
      <source bridge='%(bridge)s'/>
      <model type='virtio'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x03' function='0x0'/>
    </interface>
    <serial type='pty'>
      <target port='0'/>
    </serial>
    <console type='pty'>
      <target type='serial' port='0'/>
    </console>
    <channel type='unix'>
      <source mode='bind' path='/var/lib/libvirt/qemu/channel/target/%(name)s.org.qemu.guest_agent.0'/>
      <target type='virtio' name='org.qemu.guest_agent.0'/>
      <address type='virtio-serial' controller='0' bus='0' port='1'/>
    </channel>
    <channel type='spicevmc'>
      <target type='virtio' name='com.redhat.spice.0'/>
      <address type='virtio-serial' controller='0' bus='0' port='2'/>
    </channel>
    <input type='tablet' bus='usb'/>
    <input type='mouse' bus='ps2'/>
    <input type='keyboard' bus='ps2'/>
    <graphics type='vnc' port='-1' autoport='yes' listen='0.0.0.0'>
      <listen type='address' address='0.0.0.0'/>
    </graphics>
    <sound model='ich6'>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x04' function='0x0'/>
    </sound>
    <video>
      <model type='qxl' ram='65536' vram='65536' vgamem='16384' heads='1'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x0'/>
    </video>
    <redirdev bus='usb' type='spicevmc'>
    </redirdev>
    <redirdev bus='usb' type='spicevmc'>
    </redirdev>
    <memballoon model='virtio'>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x08' function='0x0'/>
    </memballoon>
  </devices>
</domain>
'''
