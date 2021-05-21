from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from compute.managers import CenterManager, GroupManager, ComputeError
from .models import Vdisk
from .models import Quota
from utils.errors import VdiskError
from utils import errors


class VdiskManager:
    """
    虚拟硬盘管理器
    """
    VdiskError = VdiskError

    @staticmethod
    def get_vdisk_queryset():
        """
        虚拟硬盘查询集
        :return:
            QuerySet()
        """
        return Vdisk.objects.filter(deleted=False).all()

    def get_enable_vdisk_queryset(self):
        """
        所有有效的虚拟硬盘查询集
        :return:
            QuerySet()
        """
        return self.get_vdisk_queryset().filter(enable=True).all()

    def get_user_vdisk_queryset(self, user):
        """
        获取用户的硬盘查询集

        :param user: 用户对象或id
        :return:
            QuerySet()
        """
        qs = self.get_vdisk_queryset()
        return qs.filter(user=user).all()

    def get_vdisk_queryset_by_quota(self, quota):
        """
        获取硬盘存储池下的硬盘查询集

        :param quota: 硬盘存储池配额对象或id
        :return:
            QuerySet()
        """
        qs = self.get_vdisk_queryset()
        return qs.filter(quota=quota).all()

    def get_vdisk_queryset_by_quota_ids(self, quota_ids: list):
        """
        获取硬盘存储池下的硬盘查询集

        :param quota_ids: 硬盘存储池配额id list
        :return:
            QuerySet()
        """
        qs = self.get_vdisk_queryset()
        return qs.filter(quota__in=quota_ids).all()

    @staticmethod
    def get_quota_queryset():
        """
        获取硬盘存储池配额查询集
        :return:
            QuerySet()
        """
        return Quota.objects.all()

    def get_quota_queryset_by_group(self, group):
        """
        获取宿主机组下的硬盘存储池配额查询集

        :param group: 宿主机组对象或id
        :return:
            QuerySet()
        """
        return self.get_quota_queryset().filter(group=group).all()

    def get_quota_queryset_by_group_ids(self, group_ids: list):
        """
        获取宿主机组下的硬盘存储池配额查询集

        :param group_ids: 宿主机组id list
        :return:
            QuerySet()
        """
        return self.get_quota_queryset().filter(group__in=group_ids).all()

    def get_quota_ids_by_group_ids(self, group_ids: list):
        """
        获取宿主机组下的硬盘存储池配额查询集

        :param group_ids: 宿主机组id list
        :return:
            ids: list
        """
        qs = self.get_quota_queryset_by_group_ids(group_ids)
        return list(qs.values_list('id', flat=True).all())

    def get_vdisk_queryset_by_group(self, group):
        """
        宿主机组下的硬盘查询集

        :param group: 宿主机组对象或id
        :return:
            QuerySet()
        """
        quota_ids = self.get_quota_queryset_by_group(group=group).values_list('id', flat=True).all()
        qs = self.get_vdisk_queryset()
        if len(quota_ids) == 1:
            return qs.filter(quota=quota_ids[0]).all()
        return qs.filter(quota__in=quota_ids).all()

    def get_vdisk_queryset_by_center(self, center):
        """
        分中心下的硬盘查询集

        :param center: 分中心对象或id
        :return:
            QuerySet()

        :raises: VdiskError
        """
        try:
            group_ids = CenterManager().get_group_ids_by_center(center)
        except ComputeError as e:
            raise VdiskError(msg=str(e))
        quota_ids = self.get_quota_ids_by_group_ids(group_ids)
        qs = self.get_vdisk_queryset_by_quota_ids(quota_ids)
        return qs

    def get_vdisk_by_uuid(self, uuid: str, related_fields: tuple = ()):
        """
        通过uuid获取虚拟机元数据

        :param uuid: 虚拟机uuid hex字符串
        :param related_fields: 外键字段；外键字段直接一起获取，而不是惰性的用时再获取
        :return:
            Vdisk() or None     # success

        :raise:  VdiskError
        """
        qs = self.get_vdisk_queryset()
        try:
            if related_fields:
                qs = qs.select_related(*related_fields).all()
            return qs.filter(uuid=uuid).first()
        except Exception as e:
            raise VdiskError(msg=str(e))

    def create_vdisk(self, size: int, user, center, group=None, quota=None, remarks=''):
        """
        创建一个虚拟云硬盘

        备注：group和quota参数至少需要一个，优先使用quota参数；
                当只有group参数时，通过group获取quota

        :param center: 分中心对象或id
        :param group: 宿主机组对象或id
        :param quota: 硬盘所属的云硬盘CEPH存储池对象或id
        :param size: 硬盘的容量大小
        :param user: 创建硬盘的用户
        :param remarks: 备注信息
        :return:
            Vdisk()     # success

        :raises: VdiskError
        """
        if size <= 0:
            raise errors.VdiskInvalidParams(msg='创建的硬盘大小必须大于0')

        if quota:
            quota = self.schedule_by_quota(size=size, user=user, quota=quota)
        elif group or center:
            quota = self.schedule_quota(size=size, user=user, center=center, group=group)
            if not quota:
                raise errors.VdiskNotEnoughQuota(msg='没有足够的存储容量创建硬盘，或者硬盘容量超过大小限制')
        else:
            raise errors.VdiskInvalidParams(msg='至少需要一个有效的group或quota参数')

        vd = Vdisk(size=size, quota=quota, user=user, remarks=remarks)
        try:
            vd.save()  # save内会创建元数据和ceph rbd image
        except Exception as e:
            quota.free(size=size)  # 释放申请的存储资源
            raise VdiskError(msg=str(e))

        return vd

    @staticmethod
    def schedule_by_quota(size: int, user, quota):
        """
        向硬盘CEPH存储池申请分配disk资源

        :param size:
        :param user:
        :param quota: 硬盘所属的云硬盘CEPH存储池对象或id
        :return:
            Quota()

        :raises: VdiskError
        """
        if isinstance(quota, int):
            quota = Quota.objects.filter(id=quota).first()

        if not isinstance(quota, Quota):
            raise errors.VdiskInvalidParams(msg='无效的quota或quota id')

        if not quota.user_has_perm(user):
            raise errors.VdiskAccessDenied(msg='您没有此资源池的使用权限')

        if not quota.check_disk_size_limit(size=size):
            raise errors.VdiskTooLarge(msg='超出了可创建硬盘最大容量')

        if not quota.meet_needs(size=size):
            raise errors.VdiskNotEnoughQuota(msg='没有足够的存储容量创建硬盘')

        # 向硬盘CEPH存储池申请容量
        if not quota.claim(size=size):
            raise VdiskError(msg='申请硬盘存储容量失败')

        return quota

    def schedule_quota(self, size: int, user, center=None, group=None):
        """
        分配合适的硬盘CEPH存储池

        :param size:
        :param user:
        :param center:
        :param group:
        :return:
            Quota()     #
            None        # 没有合适的硬盘CEPH存储池可用

        :raises: VdiskError
        """
        if group:
            if isinstance(group, int):
                group = GroupManager().get_group_by_id(group)
                if group is None:
                    raise errors.VdiskError.from_error(errors.NotFoundError(msg='指定的宿主机组不存在'))

            if not group.user_has_perms(user):
                raise errors.VdiskError.from_error(
                    errors.GroupAccessDeniedError())

            queryset = self.get_quota_queryset_by_group(group=group)
        elif center:
            ids = user.group_set.filter(center=center).values_list('id', flat=True)
            queryset = self.get_quota_queryset_by_group_ids(ids)
        else:
            raise errors.VdiskInvalidParams(msg='必须指定一个"group"或者"center"')

        schedule_quota = None
        for quota in queryset:
            if not quota.check_disk_size_limit(size=size):
                continue

            if not quota.meet_needs(size=size):
                continue

            # 向硬盘CEPH存储池申请容量
            if not quota.claim(size=size):
                continue

            schedule_quota = quota
            break

        if schedule_quota:
            return schedule_quota

        return None

    @staticmethod
    def mount_to_vm(vdisk_uuid: str, vm, dev):
        """
        标记虚拟硬盘挂载到虚拟机,只是在硬盘元数据层面和虚拟机建立挂载关系

        :param vdisk_uuid: 虚拟硬盘uuid
        :param vm: 虚拟机对象
        :param dev:
        :return:
            True

        :raises: VdiskError
        """
        try:
            with transaction.atomic():
                disk = Vdisk.objects.select_for_update().get(pk=vdisk_uuid)
                # 硬盘已被挂载
                if disk.vm:
                    # 已挂载到此虚拟机
                    if disk.vm == vm:
                        return True

                    raise VdiskError(msg='硬盘已被挂载到其他虚拟机')
                # 挂载
                if disk.enable is True:
                    disk.vm = vm
                    disk.attach_time = timezone.now()
                    disk.dev = dev
                    try:
                        disk.save(update_fields=['vm', 'dev', 'attach_time'])
                    except Exception:
                        raise VdiskError(msg='更新元数据失败')
                else:
                    raise VdiskError(msg='硬盘已暂停使用')
        except Vdisk.DoesNotExist as e:
            raise VdiskError(msg='硬盘不存在')
        return True

    @staticmethod
    def umount_from_vm(vdisk_uuid: str):
        """
        从虚拟机卸载虚拟硬盘,只是在硬盘元数据层面和虚拟机解除挂载关系

        :param vdisk_uuid: 虚拟硬盘uuid
        :return:
            True

        :raises: VdiskError
        """
        try:
            with transaction.atomic():
                disk = Vdisk.objects.select_for_update().get(pk=vdisk_uuid)
                # 硬盘未挂载
                if not disk.vm:
                    return True

                # 卸载
                disk.vm = None
                disk.dev = ''
                disk.attach_time = None
                try:
                    disk.save(update_fields=['vm', 'dev', 'attach_time'])
                except Exception:
                    raise VdiskError(msg='更新元数据失败')
        except Vdisk.DoesNotExist as e:
            raise VdiskError(msg='硬盘不存在')
        return True

    @staticmethod
    def umount_all_from_vm(vm_uuid: str):
        """
        从虚拟机卸载所有虚拟硬盘,只是在硬盘元数据层面和虚拟机解除挂载关系

        :param vm_uuid: 虚拟机uuid
        :return:
            rows: int   # 卸载数量

        :raises: VdiskError
        """
        with transaction.atomic():
            try:
                rows = Vdisk.objects.select_for_update().filter(vm=vm_uuid).update(vm='', dev=None)
            except Exception:
                raise VdiskError(msg='更新元数据失败')

        return rows

    def get_vm_vdisk_queryset(self, vm_uuid: str):
        """
        获取挂载到指定虚拟机下的所有虚拟硬盘查询集

        :param vm_uuid: 虚拟机uuid
        :return:
            QuerySet()
        """
        return self.get_vdisk_queryset().filter(vm=vm_uuid).all()

    def get_vm_mounted_vdisk_count(self, vm_uuid: str):
        """
        获取虚拟机下已挂载虚拟硬盘的数量

        :param vm_uuid: 虚拟机uuid
        :return:
            int
        """
        qs = self.get_vm_vdisk_queryset(vm_uuid=vm_uuid)
        return qs.count()

    def filter_vdisk_queryset(self, center_id: int = 0, group_id: int = 0, quota_id: int = 0, user_id: int = 0,
                              search: str = '', all_no_filters: bool = False, related_fields: tuple = ()):
        """
        通过条件筛选虚拟机查询集

        :param center_id: 分中心id,大于0有效
        :param group_id: 宿主机组id,大于0有效
        :param quota_id: 硬盘存储池配额id,大于0有效
        :param user_id: 用户id,大于0有效
        :param search: 关键字筛选条件
        :param all_no_filters: 筛选条件都无效时；True: 返回所有； False: 抛出错误
        :param related_fields: 外键字段；外键字段直接一起获取，而不是惰性的用时再获取
        :return:
            QuerySet    # success

        :raise: VdiskError
        """
        if not related_fields:
            related_fields = ('user', 'quota', 'quota__group', 'vm', 'vm__mac_ip')

        if center_id <= 0 and group_id <= 0 and quota_id <= 0 and user_id <= 0 and not search:
            if not all_no_filters:
                raise VdiskError(msg='查询条件无效')

            return self.get_vdisk_queryset().select_related(*related_fields).all()

        queryset = None
        if quota_id > 0:
            queryset = self.get_vdisk_queryset_by_quota(quota=quota_id)
        elif group_id > 0:
            queryset = self.get_vdisk_queryset_by_group(group_id)
        elif center_id > 0:
            queryset = self.get_vdisk_queryset_by_center(center_id)

        if user_id > 0:
            if queryset is not None:
                queryset = queryset.filter(user=user_id).all()
            else:
                queryset = self.get_user_vdisk_queryset(user_id)

        if search:
            if queryset is not None:
                queryset = queryset.filter(Q(remarks__icontains=search) | Q(uuid__icontains=search)).all()
            else:
                queryset = self.get_vdisk_queryset().filter(
                    Q(remarks__icontains=search) | Q(uuid__icontains=search)).all()

        return queryset.select_related(*related_fields).all()

    def modify_vdisk_remarks(self, uuid: str, remarks: str, user):
        """
        修改硬盘的备注信息

        :param uuid: 硬盘uuid
        :param remarks: 新的备注信息
        :param user: 用户
        :return:
            Vdisk() # success
        :raise:  VdiskError
        """
        disk = self.get_vdisk_by_uuid(uuid=uuid)
        if not disk:
            raise errors.VdiskNotExist()

        if not disk.user_has_perms(user):
            raise errors.VdiskAccessDenied(msg='没有权限访问此硬盘')

        disk.remarks = remarks
        try:
            disk.save(update_fields=['remarks'])
        except Exception as e:
            raise VdiskError(msg=str(e))

        return disk
