from django.db import transaction
from django.utils import timezone

from .models import PCIDevice
from utils.errors import DeviceError


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
        address = db.address.split(':')
        if len(address) != 4:
            raise DeviceError(msg='DEVICE BDF设备号有误')
        self._domain = address[0]
        self._bus = address[1]
        self._slot = address[2]
        self._function = address[3]
        super().__init__(db)

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
            'managed': 'yes',
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
    pass
