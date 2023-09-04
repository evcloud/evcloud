from django.db import transaction
from django.utils import timezone
from utils import errors
from vms.xml import XMLEditor
from vms.xml_builder import VmXMLBuilder
from .models import PCIDevice
from utils.errors import DeviceError
from vms.vm_builder import get_vm_domain


class BaseDevice:
    def __init__(self, db):
        self._db = db

    def user_has_perms(self, user):
        """
        用户是否有访问此设备的权限

        :param user: 用户
        :return:
            True    # has
            False   # no
        """
        return self._db.user_has_perms(user)

    def set_remarks(self, content: str):
        """
        设置设备备注信息

        :param content: 备注信息
        :return:
            True    # success
            False   # failed
        """
        return self._db.set_remarks(content=content)

    @property
    def type_name(self):
        return self._db.type_display

    @property
    def host_ipv4(self):
        return self._db.host.ipv4

    @property
    def host_id(self):
        return self._db.host_id

    @property
    def group_id(self):
        return self._db.host.group_id

    @property
    def address(self):
        return self._db.address

    @property
    def vm(self):
        return self._db.vm

    @property
    def id(self):
        return self._db.id

    @property
    def attach_time(self):
        return self._db.attach_time

    @property
    def enable(self):
        return self._db.enable

    @property
    def remarks(self):
        return self._db.remarks

    @property
    def device(self):
        return self._db


class BasePCIDevice(BaseDevice):
    def __init__(self, db):
        if db.type in [1, 2, 3]:  # PCIe网卡/PCIe硬盘/PCIeGPU
            address = db.address.split(':')
            if len(address) != 4:
                raise DeviceError(msg='DEVICE BDF设备号有误')
            self._domain = address[0]
            self._bus = address[1]
            self._slot = address[2]
            self._function = address[3]
        super().__init__(db)  # 本地硬盘

    @property
    def domain(self):
        return self._domain

    @property
    def bus(self):
        return self._bus

    @property
    def slot(self):
        return self._slot

    @property
    def function(self):
        return self._function

    @property
    def xml_tpl(self):
        return """
            <hostdev mode='%(mode)s' type='%(type)s' managed='yes'>
                <source>
                    <address domain='0x%(domain)s' bus='0x%(bus)s' slot='0x%(slot)s' function='0x%(function)s'/>
                </source>
            </hostdev>
            """

    @property
    def xml_desc(self):
        return self.xml_tpl % {
            'mode': 'subsystem',
            'type': 'pci',
            'domain': self.domain,
            'bus': self.bus,
            'slot': self.slot,
            'function': self.function
        }

    def need_in_same_host(self):
        """
        设备是否需要与挂载的虚拟机在用同一个宿主机上
        """
        return self._db.need_in_same_host()

    def mount(self, vm):
        """
        设备元数据层面与虚拟机建立挂载关系

        :return:
            True                # success
            raise DeviceError   # failed

        :raise: DeviceError
        """
        try:
            with transaction.atomic():
                db = PCIDevice.objects.select_for_update().get(pk=self._db.pk)
                if not db.enable:
                    raise DeviceError(msg='设备未开启使用')

                if db.vm_id == vm.hex_uuid:
                    return True

                if db.vm_id:
                    raise DeviceError(msg='设备已被挂载于其他主机')

                db.vm = vm
                db.attach_time = timezone.now()
                db.save(update_fields=['vm', 'attach_time'])
                self._db = db
                return True
        except Exception as e:
            raise DeviceError(msg=str(e))

    def umount(self):
        """
        设备元数据层面与虚拟机解除挂载关系

        :return:
            True                # success
            raise DeviceError   # failed

        :raise: DeviceError
        """
        try:
            with transaction.atomic():
                db = PCIDevice.objects.select_for_update().get(pk=self._db.pk)
                if not db.vm_id:
                    return True

                db.vm = None
                db.attach_time = None
                db.save(update_fields=['vm', 'attach_time'])
                self._db = db
                return True
        except Exception as e:
            raise DeviceError(msg=str(e))

    def set_enable(self):
        res = True
        try:
            with transaction.atomic():
                db = PCIDevice.objects.select_for_update().get(pk=self._db.pk)
                db.enable = True
                db.save(update_fields=['enable'])
                self._db = db
        except Exception:
            res = False
        return res 

    def set_disable(self):
        res = True
        try:
            with transaction.atomic():
                db = PCIDevice.objects.select_for_update().get(pk=self._db.pk)
                db.enable = False
                db.save(update_fields=['enable'])
                self._db = db
        except Exception:
            res = False
        return res 


class GPUDevice(BasePCIDevice):
    """
    GPU设备
    """

    def xml_desc(self):
        return self.xml_tpl % {
            'mode': 'subsystem',
            'type': 'pci',
            'domain': self.domain,
            'bus': self.bus,
            'slot': self.slot,
            'function': self.function
        }


class HardDiskDevice(BasePCIDevice):
    """
    本地硬盘设备
    """

    def __init__(self, db):
        self.dev_drive = db.address
        super().__init__(db)

    def _vm_domain(self, vm):
        self._vm_domain = get_vm_domain(vm=vm)
        return self._vm_domain

    def xml_tpl(self):
        """本地硬盘xml模板"""
        return """
                <disk type='block' device='disk'>
                  <driver name='qemu' type='raw' cache='none' io='native' discard='unmap'/>
                  <source dev='{dev_drive}'/>
                  <target dev='{dev}' bus='{bus}'/>
                </disk>
            """

    def xml_desc(self, bus='virtio'):
        if self.vm is None:
            raise DeviceError(msg='vm 不能为None')

        dev = self.get_dev_drive()
        return self.xml_tpl().format(dev=dev, bus=bus, dev_drive=self.dev_drive)

    def get_dev_drive(self):
        """
        获取盘符

        return: dev 盘符

        """
        if self.vm is None:
            raise errors.VmNotExistError(msg='无效的虚拟机')

        xml_desc = self._vm_domain(vm=self.vm).xml_desc()
        source_list, dev_list, disk_dev = self.get_vm_vdisk_dev_list(xml_desc=xml_desc)
        if self.dev_drive in source_list:

            return disk_dev[self.dev_drive]

        dev = VmXMLBuilder().new_vdisk_dev(dev_list)
        if not dev:
            raise errors.VmTooManyVdiskMounted()

        return dev

    def get_vm_vdisk_dev_list(self, xml_desc: str):
        """
        获取虚拟机所有硬盘的dev

        :param xml_desc: 虚拟机xml
        :return:
            (disk:list, dev:list)    # disk = [disk_uuid, disk_uuid, ]; dev = ['vda', 'vdb', ]

        :raises: VmError
        """
        dev_list = []
        source_list = []
        disk_dev = {}
        xml = XMLEditor()
        if not xml.set_xml(xml_desc):
            raise errors.VmError(msg='虚拟机xml文本无效')

        root = xml.get_root()
        devices = root.getElementsByTagName('devices')[0].childNodes
        for d in devices:
            if d.nodeName == 'disk':
                source_disk = None
                target_dev = None
                for disk_child in d.childNodes:
                    if disk_child.nodeName == 'source':
                        source_disk = disk_child.getAttribute('dev')
                        source_list.append(source_disk)
                    if disk_child.nodeName == 'target':
                        target_dev = disk_child.getAttribute('dev')
                        dev_list.append(target_dev)

                if source_disk is None or source_disk == '':
                    source_disk = 'system_disk'

                if source_disk in disk_dev:
                    raise errors.VdiskError(msg='重复的盘符')

                disk_dev[source_disk] = target_dev

        return source_list, dev_list, disk_dev
