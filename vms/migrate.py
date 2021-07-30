from datetime import timedelta

import libvirt
from django.utils import timezone

from compute.managers import HostManager
from utils.ev_libvirt.virt import (
    VirtError, VmDomain, VirDomainNotExist, VirHostDown, VirtHost
)
from utils import errors
from .models import (Vm, MigrateTask)
from .tasks import creat_migrate_vm_task


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

    def live_migrate_vm(self, vm: Vm, dest_host_id: int):
        """
        迁移虚拟机

        :param vm: 虚拟机元数据对象
        :param dest_host_id: 目标宿主机id
        :return:
            MigrateTask()   # success

        :raises: VmError
        """
        vm_uuid = vm.get_uuid()
        if vm.disk_type == vm.DiskType.LOCAL:
            raise errors.VmError.from_error(
                errors.Unsupported(msg='虚拟主机为本地硬盘，不支持迁移'))

        # 2m内有未完成的迁移任务
        if vm.migrate_log_set.filter(status=MigrateTask.Status.IN_PROCESS,
                                     migrate_time__lt=(timezone.now() - timedelta(minutes=2))).exists():
            raise errors.VmError(msg=f'此虚拟机正在迁移, 未防止迁移冲突,请等待一段时间后重试')

        # 是否有迁移任务需要善后工作
        task_qs = vm.migrate_log_set.filter(status=MigrateTask.Status.SOME_TODO).order_by('-id').all()
        if len(task_qs) > 1:
            raise errors.VmError(msg=f'此虚拟机有多个未完成的迁移任务，迁移善后工作请先联系管理员手动处理。')
        m_log = task_qs.first()
        if m_log is not None:
            try:
                if not self.handle_some_todo_migrate_log(task_log=m_log):
                    raise errors.VmError()
            except errors.VmError as e:
                raise errors.VmError(msg=f'此虚拟机有未完成的迁移任务，迁移善后工作请先联系管理员手动处理。')

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
        dest_vm_host = VirtHost(host_ipv4=dest_host.ipv4)
        try:
            dest_conn = dest_vm_host.get_connection()
        except VirHostDown as e:
            raise errors.VmError(msg=f'无法连接宿主机,{str(e)}')
        except VirtError as e:
            raise errors.VmError(msg=f'连接宿主机失败,{str(e)}')

        # PCI设备
        pci_devices = vm.pci_devices
        if pci_devices:
            raise errors.VmError(msg='请先卸载主机挂载的PCI设备')

        m_task = MigrateTask(vm=vm, vm_uuid=vm_uuid, src_host=src_host, src_host_ipv4=src_host.ipv4,
                             dst_host=dest_host, dst_host_ipv4=dest_host.ipv4, migrate_time=timezone.now(),
                             tag=MigrateTask.Tag.MIGRATE_LIVE, status=MigrateTask.Status.IN_PROCESS)

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

        r = creat_migrate_vm_task(self.live_migrate_vm_task, vm=vm, m_task=m_task, src_domain=src_domain,
                                  dest_conn=dest_conn)
        if r is not None:
            dest_host.free(vcpu=vm.vcpu, mem=vm.mem)
            m_task.delete()
            raise errors.VmError(msg=f'创建迁移任务错误,{str(r)}')

        return m_task

    @staticmethod
    def live_migrate_vm_task(vm, m_task: MigrateTask, src_domain: VmDomain, dest_conn: libvirt.virConnect):
        dest_host = m_task.dst_host
        src_host = m_task.src_host

        # 迁移虚拟机
        try:
            src_domain.live_migrate(dest_host_conn=dest_conn, undefine_source=True)
        except Exception as e:
            # 释放目标宿主机资源
            if dest_host.free(vcpu=vm.vcpu, mem=vm.mem):
                m_task.dst_is_claim = False

            m_task.status = m_task.Status.FAILED
            m_task.content = str(e)
            m_task.do_save()
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
