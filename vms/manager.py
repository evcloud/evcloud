from django.db.models import Q

from compute.managers import CenterManager, GroupManager, ComputeError
from .models import (Vm, VmArchive, VmLog, Flavor)
from utils.errors import VmError


class VmManager:
    """
    虚拟机元数据管理器
    """
    VmError = VmError

    def get_vm_by_uuid(self, vm_uuid: str, related_fields: tuple = ('mac_ip', 'host')):
        """
        通过uuid获取虚拟机元数据

        :param vm_uuid: 虚拟机uuid hex字符串
        :param related_fields: 外键字段；外键字段直接一起获取，而不是惰性的用时再获取
        :return:
            Vm() or None     # success

        :raise:  VmError
        """
        qs = self.get_vms_queryset()
        try:
            if related_fields:
                qs = qs.select_related(*related_fields).all()
            return qs.filter(uuid=vm_uuid).first()
        except Exception as e:
            raise VmError(msg=str(e))

    @staticmethod
    def get_vms_queryset():
        """
        获取所有虚拟机的查询集
        :return: QuerySet()
        """
        return Vm.objects.all()

    def get_user_vms_queryset(self, user):
        """
        获取用户的虚拟机查询集
        :param user: 用户
        :return: QuerySet()
        """
        return self.get_vms_queryset().filter(user=user).all()

    @staticmethod
    def get_vms_queryset_by_center(center_or_id):
        """
        获取分中心下的虚拟机查询集

        :param center_or_id: 分中心对象或id
        :return:
            vms: QuerySet   # success
        :raise VmError
        """
        try:
            group_ids = CenterManager().get_group_ids_by_center(center_or_id)
            host_ids = GroupManager().get_host_ids_by_group_ids(group_ids)
        except ComputeError as e:
            raise VmError(msg=str(e))

        return Vm.objects.filter(host__in=host_ids).all()

    @staticmethod
    def get_vms_queryset_by_group(group_or_id):
        """
        获取宿主机组下的虚拟机查询集

        :param group_or_id: 宿主机组对象或id
        :return:
            vms: QuerySet   # success
        :raise VmError
        """
        try:
            host_ids = GroupManager().get_all_host_ids_by_group(group_or_id)
        except ComputeError as e:
            raise VmError(msg=str(e))

        return Vm.objects.filter(host__in=host_ids).all()

    @staticmethod
    def get_vms_queryset_by_host(host_or_id):
        """
        获取宿主机下的虚拟机查询集

        :param host_or_id: 宿主机对象或id
        :return:
            vms: QuerySet   # success
        :raise VmError
        """
        return Vm.objects.filter(host=host_or_id).all()

    def filter_vms_queryset(self, center_id: int = 0, group_id: int = 0, host_id: int = 0, user_id: int = 0,
                            search: str = '', all_no_filters: bool = False, related_fields: tuple = ()):
        """
        通过条件筛选虚拟机查询集

        :param center_id: 分中心id,大于0有效
        :param group_id: 宿主机组id,大于0有效
        :param host_id: 宿主机id,大于0有效
        :param user_id: 用户id,大于0有效
        :param search: 关键字筛选条件
        :param all_no_filters: 筛选条件都无效时；True: 返回所有； False: 抛出错误
        :param related_fields: 外键字段；外键字段直接一起获取，而不是惰性的用时再获取
        :return:
            QuerySet    # success

        :raise: VmError
        """
        if not related_fields:
            related_fields = ('user', 'image', 'mac_ip__vlan', 'host')

        if center_id <= 0 and group_id <= 0 and host_id <= 0 and user_id <= 0 and not search:
            if not all_no_filters:
                raise VmError(msg='查询虚拟机条件无效')
            return self.get_vms_queryset().select_related(*related_fields).all()

        vm_queryset = None
        if host_id > 0:
            vm_queryset = self.get_vms_queryset_by_host(host_id)
        elif group_id > 0:
            vm_queryset = self.get_vms_queryset_by_group(group_id)
        elif center_id > 0:
            vm_queryset = self.get_vms_queryset_by_center(center_id)

        if user_id > 0:
            if vm_queryset is not None:
                vm_queryset = vm_queryset.filter(user=user_id).all()
            else:
                vm_queryset = self.get_user_vms_queryset(user_id)

        if search:
            if vm_queryset is not None:
                vm_queryset = vm_queryset.filter(Q(remarks__icontains=search) | Q(mac_ip__ipv4__icontains=search) |
                                                 Q(uuid__icontains=search)).all()
            else:
                vm_queryset = Vm.objects.filter(Q(remarks__icontains=search) | Q(mac_ip__ipv4__icontains=search) |
                                                Q(uuid__icontains=search)).all()

        return vm_queryset.select_related(*related_fields).all()


class VmArchiveManager:
    """
    虚拟机归档管理类
    """
    VmError = VmError

    @staticmethod
    def add_vm_archive(vm: Vm):
        """
        添加一个虚拟机的归档记录

        :param vm: 虚拟机元数据对象
        :return:
            VmArchive() # success

        :raises:  VmError
        """
        try:
            host = vm.host
            group = host.group
            center = group.center
            mac_ip = vm.mac_ip
            vlan = mac_ip.vlan
            image = vm.image
            ceph_pool = image.ceph_pool

            va = VmArchive(uuid=vm.get_uuid(), name=vm.name, vcpu=vm.vcpu, mem=vm.mem, disk=vm.disk, xml=vm.xml,
                           mac=mac_ip.mac, ipv4=mac_ip.ipv4, vlan_id=vlan.id, br=vlan.br,
                           image_id=image.id, image_parent=image.base_image, ceph_id=ceph_pool.ceph.id,
                           ceph_pool=ceph_pool.pool_name, center_id=center.id, center_name=center.name,
                           group_id=group.id, group_name=group.name, host_id=host.id, host_ipv4=host.ipv4,
                           user=vm.user, create_time=vm.create_time, remarks=vm.remarks, disk_type=vm.disk_type,
                           sys_disk_size=vm.sys_disk_size)
            va.save()
        except Exception as e:
            raise VmError(msg=str(e))
        return va

    @staticmethod
    def get_vm_archive(vm: Vm):
        return VmArchive.objects.filter(uuid=vm.get_uuid()).first()


class VmLogManager:
    """
    虚拟机错误日志记录管理
    """
    def __init__(self):
        self.vm_log = VmLog()

    @property
    def about(self):
        return self.vm_log

    @staticmethod
    def add_log(title: str, about: int, text: str):
        """
        添加记录

        :param title: 记录标题
        :param about: 记录相关内容
        :param text: 记录内容
        :return:
            VmLog()     # success
            None        # failed
        """
        about = VmLog.to_valid_about_value(about)
        try:
            log = VmLog(title=title, about=about, content=text)
            log.save()
        except Exception as e:
            return None

        return log


class FlavorManager:

    VmError = VmError

    def get_flavor_by_id(self, f_id: int):
        """
        通过uuid获取虚拟机元数据

        :param f_id:
        :return:
            Flavor() or None     # success

        :raise:  VmError
        """
        qs = self.get_flaver_queryset()
        try:
            return qs.filter(id=f_id).first()
        except Exception as e:
            raise VmError(msg=str(e))

    @staticmethod
    def get_flaver_queryset():
        """
        激活的样式
        :return: QuerySet()
        """
        return Flavor.objects.filter(enable=True).all()

    @staticmethod
    def get_public_flaver_queryset():
        """
        公开激活的样式

        :return: QuerySet()
        """
        return Flavor.objects.filter(enable=True, public=True).all()

    def get_user_flaver_queryset(self, user):
        """
        用户对应权限激活的样式

        :return: QuerySet()
        """
        if user.is_superuser:
            return self.get_flaver_queryset()
        return self.get_public_flaver_queryset()
