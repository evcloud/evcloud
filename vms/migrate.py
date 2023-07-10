from datetime import timedelta

from django.utils import timezone
from django.db import transaction

from compute.managers import HostManager
from vdisk.manager import VdiskManager
from utils.ev_libvirt.virt import (
    VirtError, VmDomain, VirDomainNotExist, VirHostDown, VirtHost
)
from utils import errors
from .models import (Vm, MigrateTask)
from .tasks import creat_migrate_vm_task
from .vm_builder import VmBuilder, get_vm_domain


class VmMigrateManager:
    @staticmethod
    def get_migrate_task(_id, user):
        task = MigrateTask.objects.select_related('vm').filter(id=_id).first()
        if task is None:
            return None

        if user.is_superuser:
            return task

        if task.vm is None:
            return task

        if task.vm.user_id == user.id:
            return task

        raise errors.AccessDeniedError(msg='你没有权限查询此迁移任务状态')

    def _vm_old_task_check(self, vm):
        """
        vm是否有旧迁移任务，旧任务是否需要善后工作

        :raises: VmError
        """
        # 5m内有等待和正在迁移的迁移任务
        task = vm.migrate_log_set.filter(
            status__in=[MigrateTask.Status.IN_PROCESS, MigrateTask.Status.WAITING],
            migrate_time__lt=(timezone.now() - timedelta(minutes=5))).first()
        if task:
            if task.status == MigrateTask.Status.WAITING:
                raise errors.VmError(msg=f'此虚拟机正在等待迁移, 未防止迁移冲突,请等待一段时间后重试')

            raise errors.VmError(msg=f'此虚拟机正在迁移, 未防止迁移冲突,请等待一段时间后重试')

        # 是否有迁移任务需要善后工作
        task_qs = vm.migrate_log_set.select_related('vm', 'dst_host').filter(
            status__in=[MigrateTask.Status.SOME_TODO, MigrateTask.Status.WAITING]
        ).order_by('-id').all()
        some_todo_tasks = []
        for task in task_qs:
            if task.status == MigrateTask.Status.WAITING:
                self._do_task_failed(m_task=task, message='task waiting, not migrate')
            else:
                some_todo_tasks.append(task)

        if len(some_todo_tasks) > 1:
            raise errors.VmError(msg=f'此虚拟机有多个未完成的迁移任务，迁移善后工作请先联系管理员手动处理。')

        if some_todo_tasks:
            try:
                if not self.handle_some_todo_migrate_log(task_log=some_todo_tasks[0]):
                    raise errors.VmError()
            except errors.VmError as e:
                raise errors.VmError(msg=f'此虚拟机有未完成的迁移任务，迁移善后工作请先联系管理员手动处理。')

    def _pre_live_migrate(self, vm, dest_host_id: int):
        """
        动态迁移前工作
        :return:
            Host()      # 目标宿主机

        :raises: VmError
        """
        vm_uuid = vm.get_uuid()
        if vm.disk_type == vm.DiskType.LOCAL:
            raise errors.VmError.from_error(
                errors.Unsupported(msg='虚拟主机为本地硬盘，不支持迁移'))

        self._vm_old_task_check(vm)

        # 虚拟机的状态
        host = vm.host
        try:
            src_domain = VmDomain(host_ip=host.ipv4, vm_uuid=vm_uuid)
            if not src_domain.is_running():
                raise errors.VmError.from_error(err=errors.Unsupported(msg='主机没有运行，无法进行动态迁移'))
        except VirHostDown as e:
            raise errors.VmError(msg=f'无法连接宿主机,{str(e)}')
        except VirDomainNotExist as e:
            raise errors.VmError(msg=f'虚拟机不存在,无法动态迁移,{str(e)}')
        except VirtError as e:
            raise errors.VmError(msg=f'获取虚拟机运行状态失败,{str(e)}')

        # 是否同宿主机组
        src_host = vm.host
        try:
            dest_host = HostManager.get_host_by_id(host_id=dest_host_id)
        except errors.ComputeError as e:
            raise errors.VmError(msg=str(e))
        if not dest_host:
            raise errors.VmError(msg='指定的目标宿主机不存在')

        if src_host.id == dest_host.id:
            raise errors.VmError(msg='不能在同一个宿主机上迁移')
        if dest_host.group_id != src_host.group_id:
            raise errors.VmError(msg='目标宿主机和云主机宿主机不在同一个机组')

        # 检测目标宿主机是否处于活动状态
        try:
            VirtHost(host_ipv4=dest_host.ipv4).get_connection()
        except VirHostDown as e:
            raise errors.VmError(msg=f'无法连接宿主机,{str(e)}')
        except VirtError as e:
            raise errors.VmError(msg=f'连接宿主机失败,{str(e)}')

        # PCI设备
        pci_devices = vm.pci_devices
        if pci_devices:
            raise errors.VmError(msg='请先卸载主机挂载的PCI设备')

        att_ip = vm.get_attach_ip()
        if att_ip:
            raise errors.VmError(msg='请先分离主机附加的IP')

        return dest_host

    def live_migrate_vm(self, vm: Vm, dest_host_id: int):
        """
        迁移虚拟机

        :param vm: 虚拟机元数据对象
        :param dest_host_id: 目标宿主机id
        :return:
            MigrateTask()   # success

        :raises: VmError
        """
        dest_host = self._pre_live_migrate(vm=vm, dest_host_id=dest_host_id)

        vm_uuid = vm.get_uuid()
        src_host = vm.host
        m_task = MigrateTask(vm=vm, vm_uuid=vm_uuid, src_host=src_host, src_host_ipv4=src_host.ipv4,
                             dst_host=dest_host, dst_host_ipv4=dest_host.ipv4, migrate_time=timezone.now(),
                             tag=MigrateTask.Tag.MIGRATE_LIVE, status=MigrateTask.Status.WAITING)

        # 目标宿主机资源申请
        try:
            dest_host = HostManager.claim_from_host(host_id=dest_host_id, vcpu=vm.vcpu, mem=vm.mem)
        except errors.ComputeError as e:
            raise errors.VmError(msg=str(e))

        m_task.dst_is_claim = True
        r = m_task.do_save()
        if r is not None:
            dest_host.free(vcpu=vm.vcpu, mem=vm.mem)
            raise errors.VmError(msg=f'创建迁移任务记录错误,{str(r)}')

        r = creat_migrate_vm_task(self.live_migrate_vm_task, m_task_id=m_task.id)
        if isinstance(r, Exception):
            dest_host.free(vcpu=vm.vcpu, mem=vm.mem)
            m_task.delete()
            raise errors.VmError(msg=f'创建迁移任务错误,{str(r)}')

        return m_task

    @staticmethod
    def _do_task_failed(m_task, message: str):
        """
        :raises: VmError
        """
        vm = m_task.vm
        dest_host = m_task.dst_host
        # 释放目标宿主机资源
        if dest_host.free(vcpu=vm.vcpu, mem=vm.mem):
            m_task.dst_is_claim = False

        m_task.status = m_task.Status.FAILED
        m_task.content = message
        r = m_task.do_save(update_fields=['dst_is_claim', 'status', 'content'])
        if r is not None:
            raise errors.VmError.from_error(r)

    @staticmethod
    def live_migrate_vm_task(m_task_id):
        with transaction.atomic():
            m_task = MigrateTask.objects.select_for_update().select_related(
                'vm', 'src_host', 'dst_host').filter(id=m_task_id).first()
            if m_task is None:
                return

            if m_task.status != m_task.Status.WAITING:
                return

            m_task.status = m_task.Status.IN_PROCESS
            m_task.do_save(update_fields=['status'])

        VmMigrateManager._live_migrate_vm_task(m_task)

    @staticmethod
    def _live_migrate_vm_task(m_task):
        # 迁移虚拟机
        try:
            dest_host = m_task.dst_host
            src_host = m_task.src_host
            vm = m_task.vm
            dest_vm_host = VirtHost(host_ipv4=m_task.dst_host_ipv4)
            try:
                dest_conn = dest_vm_host.get_connection()
            except VirHostDown as e:
                raise errors.VmError(msg=f'无法连接宿主机,{str(e)}')
            except VirtError as e:
                raise errors.VmError(msg=f'连接宿主机失败,{str(e)}')

            src_domain = get_vm_domain(vm)
            src_domain.live_migrate(dest_host_conn=dest_conn, undefine_source=True)
        except Exception as e:
            VmMigrateManager._do_task_failed(m_task=m_task, message=str(e))
            return

        log_msg = ''
        # vm元数据更新关联目标宿主机
        try:
            vm.host = dest_host
            vm.save(update_fields=['host'])
        except Exception as e:
            log_msg += f'vm(uuid={vm.hex_uuid})已从源host({src_host.ipv4})动态迁移到目标宿主机(id={dest_host.id}, ' \
                       f'ipv4={dest_host.ipv4}), 但是vm元数据更新关联目标宿主机失败，err={str(e)};\n'

        dest_host.vm_created_num_add_1()  # 宿主机虚拟机数+1

        # 标记原宿主机上的虚拟机已删除
        try:
            m_task.src_undefined = True
            m_task.status = m_task.Status.SOME_TODO
            m_task.do_save()
        except VirtError as e:
            log_msg += f'源host({src_host.ipv4})上的vm(uuid={vm.hex_uuid})删除失败，err={str(e)};\n'

        # 源宿主机资源释放
        src_host.vm_created_num_sub_1()  # 宿主机虚拟机数-1
        if src_host.free(vcpu=vm.vcpu, mem=vm.mem):
            m_task.src_is_free = True
            m_task.do_save()
        else:
            log_msg += f'源host({src_host.ipv4})资源(cpu={vm.vcpu}, mem={vm.mem}MB)释放失败;\n'

        # 迁移日志
        if not log_msg:
            log_msg = '迁移正常'

        m_task.status = m_task.Status.COMPLETE
        m_task.content = log_msg
        m_task.migrate_complete_time = timezone.now()
        m_task.do_save()

    @staticmethod
    def handle_some_todo_migrate_log(task_log: MigrateTask):
        """
        处理需要进行善后工作的vm迁移记录

        :return:
            True            #
            False           #
        :raises: VmError
        """
        vm = task_log.vm
        if not vm:
            return False

        # vm元数据目标host是否关联成功
        dst_host_id = task_log.dst_host_id
        if dst_host_id and vm.host_id != dst_host_id:
            # 检测vm现在关联的host是否正确
            try:
                if not VmDomain(host_ip=vm.host_ipv4, vm_uuid=vm.get_uuid()).exists():
                    if VmDomain(host_ip=task_log.dst_host_ipv4, vm_uuid=vm.get_uuid()).exists():
                        vm.host_id = dst_host_id
                        vm.save(update_fields=['host_id'])
                    else:
                        raise errors.VmError(msg='源宿主机和目标宿主机上都未查询到虚拟机，无法处理此迁移任务善后工作')
            except Exception as e:
                raise errors.VmError(msg=f'{str(e)}')

        ok = True
        # 是否已清理源云主机
        if not task_log.src_undefined:
            ok = False

        # 是否释放源宿主机资源配额
        if not task_log.src_is_free:
            if task_log.src_host.free(vcpu=vm.vcpu, mem=vm.mem):
                task_log.src_is_free = True
                task_log.do_save()
            else:
                ok = False

        if ok:
            task_log.status = task_log.Status.COMPLETE
            task_log.do_save()

        return ok

    @staticmethod
    def _pre_static_migrite(vm: Vm, host_id: int, force: bool):
        """
        静态迁移虚拟机前处理

        :param host_id: 宿主机id
        :param force: True(强制迁移)，False(普通迁移)
        :return:
            Host()   # success

        :raises: VmError
        """
        if vm.disk_type == vm.DiskType.LOCAL:
            raise errors.VmError.from_error(
                errors.Unsupported(msg='虚拟主机为本地硬盘，不支持迁移'))

        # 虚拟机的状态
        vm_domain = get_vm_domain(vm)
        try:
            run = vm_domain.is_running()
        except VirHostDown as e:
            if not force:
                raise errors.VmError(msg=f'无法连接宿主机,{str(e)}')
        except VirDomainNotExist as e:
            pass
        except VirtError as e:
            raise errors.VmError(msg=f'获取虚拟机运行状态失败,{str(e)}')
        else:
            if run:
                if not force:
                    raise errors.VmRunningError(msg='虚拟机正在运行，请先关闭虚拟机')

                # 强制迁移，先尝试断电
                try:
                    vm_domain.poweroff()
                except VirtError as e:
                    pass

        # 是否同宿主机组
        old_host = vm.host
        try:
            new_host = HostManager.get_host_by_id(host_id=host_id)
        except errors.ComputeError as e:
            raise errors.VmError(msg=str(e))
        if not new_host:
            raise errors.VmError(msg='指定的目标宿主机不存在')

        if old_host.id == new_host.id:
            raise errors.VmError(msg='不能在同一个宿主机上迁移')
        if new_host.group_id != old_host.group_id:
            raise errors.VmError(msg='目标宿主机和云主机宿主机不在同一个机组')

        # 检测目标宿主机是否处于活动状态
        alive = VirtHost(host_ipv4=new_host.ipv4).host_alive()
        if not alive:
            raise errors.VmError(msg='目标宿主机处于未活动状态，请重新选择迁移目标宿主机')

        # PCI设备
        pci_devices = vm.pci_devices
        if pci_devices:
            if not force:
                raise errors.VmError(msg='请先卸载主机挂载的PCI设备')

            # 卸载设备
            for device in pci_devices:
                try:
                    device.umount()
                except errors.DeviceError as e:
                    raise errors.VmError(msg=f'卸载主机挂载的PCI设备失败, {str(e)}')

        att_ip = vm.get_attach_ip()
        if att_ip:
            raise errors.VmError(msg='请先分离主机附加的IP')

        return new_host

    def static_migrate(self, vm: Vm, host_id: int, force: bool = False):
        """
        静态迁移虚拟机

        :param vm: Vm对象
        :param host_id: 宿主机id
        :param force: True(强制迁移)，False(普通迁移)
        :return:
            Vm()   # success

        :raises: VmError
        """
        vm_uuid = vm.get_uuid()
        old_host = vm.host

        new_host = self._pre_static_migrite(vm=vm, host_id=host_id, force=force)
        m_log = MigrateTask(vm=vm, vm_uuid=vm_uuid, src_host=old_host, src_host_ipv4=old_host.ipv4,
                            dst_host=new_host, dst_host_ipv4=new_host.ipv4, migrate_time=timezone.now(),
                            tag=MigrateTask.Tag.MIGRATE_STATIC)

        # 目标宿主机资源申请
        try:
            new_host = HostManager.claim_from_host(host_id=host_id, vcpu=vm.vcpu, mem=vm.mem)
        except errors.ComputeError as e:
            raise errors.VmError(msg=str(e))

        m_log.dst_is_claim = True
        # 目标宿主机创建虚拟机
        try:
            vm, from_begin_create = VmBuilder.migrate_create_vm(vm=vm, new_host=new_host)
        except Exception as e:
            # 释放目标宿主机资源
            new_host.free(vcpu=vm.vcpu, mem=vm.mem)
            raise errors.VmError(msg=str(e))

        new_host.vm_created_num_add_1()  # 宿主机虚拟机数+1

        m_log.do_save()

        log_msg = ''
        if from_begin_create:   # 重新构建vm xml创建的vm, 需要重新挂载硬盘等设备
            # 向虚拟机挂载硬盘
            vdisks = vm.vdisks
            vm_domain = get_vm_domain(vm)
            for vdisk in vdisks:
                try:
                    disk_xml = vdisk.xml_desc(dev=vdisk.dev)
                    vm_domain.attach_device(xml=disk_xml)
                except (VirtError, Exception) as e:
                    log_msg += f'vdisk(uuid={vdisk.uuid}) 挂载失败,err={str(e)}；\n'
                    try:
                        VdiskManager.umount_from_vm(vdisk_uuid=vdisk.uuid)
                    except errors.VdiskError as e2:
                        log_msg += f'vdisk(uuid={vdisk.uuid})和vm(uuid={vm_uuid}元数据挂载关系解除失败),err={str(e2)}；\n'

            # 如果挂载了硬盘，更新vm元数据中的xml
            if vdisks:
                try:
                    xml_desc = vm_domain.xml_desc()
                    vm.xml = xml_desc
                    vm.save(update_fields=['xml'])
                except Exception:
                    pass

        # 删除原宿主机上的虚拟机
        try:
            ok = VmDomain(host_ip=old_host.ipv4, vm_uuid=vm_uuid).undefine()
            if ok:
                m_log.src_undefined = True
                old_host.vm_created_num_sub_1()  # 宿主机虚拟机数-1
        except VirtError as e:
            log_msg += f'源host({old_host.ipv4})上的vm(uuid={vm_uuid})删除失败，err={str(e)};\n'

        # 源宿主机资源释放
        if old_host.free(vcpu=vm.vcpu, mem=vm.mem):
            m_log.src_is_free = True
        else:
            log_msg += f'源host({old_host.ipv4})资源(vcpu={vm.vcpu}, mem={vm.mem}MB)释放失败;\n'

        # 迁移日志
        if log_msg:
            m_log.status = m_log.Status.SOME_TODO
        else:
            log_msg = '迁移正常'
            m_log.status = m_log.Status.COMPLETE

        m_log.content = log_msg
        m_log.migrate_complete_time = timezone.now()
        m_log.do_save()

        return vm
