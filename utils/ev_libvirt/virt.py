import subprocess

import libvirt


VIR_DOMAIN_NOSTATE = 0  # no state
VIR_DOMAIN_RUNNING = 1  # the domain is running
VIR_DOMAIN_BLOCKED = 2  # the domain is blocked on resource
VIR_DOMAIN_PAUSED = 3  # the domain is paused by user
VIR_DOMAIN_SHUTDOWN = 4  # the domain is being shut down
VIR_DOMAIN_SHUTOFF = 5  # the domain is shut off
VIR_DOMAIN_CRASHED = 6  # the domain is crashed
VIR_DOMAIN_PMSUSPENDED = 7  # the domain is suspended by guest power management
VIR_DOMAIN_LAST = 8  # NB: this enum value will increase over time as new events are added to the libvirt API. It reflects the last state supported by this version of the libvirt API.
VIR_DOMAIN_HOST_DOWN = 9  # host connect failed
VIR_DOMAIN_MISS = 10  # vm miss

VM_STATE = {
    VIR_DOMAIN_NOSTATE: 'no state',
    VIR_DOMAIN_RUNNING: 'running',
    VIR_DOMAIN_BLOCKED: 'blocked',
    VIR_DOMAIN_PAUSED: 'paused',
    VIR_DOMAIN_SHUTDOWN: 'shut down',
    VIR_DOMAIN_SHUTOFF: 'shut off',
    VIR_DOMAIN_CRASHED: 'crashed',
    VIR_DOMAIN_PMSUSPENDED: 'suspended',
    VIR_DOMAIN_LAST: '',
    VIR_DOMAIN_HOST_DOWN: 'host connect failed',
    VIR_DOMAIN_MISS: 'miss',
}


class VirtError(Exception):
    '''
    libvirt函数封装错误类型定义
    '''
    def __init__(self, code:int=0, msg:str='', err=None):
        '''
        :param code: 错误码
        :param msg: 错误信息
        :param err: 错误对象
        '''
        self.code = code
        self.msg = msg
        self.err = err

    def __str__(self):
        return self.detail()

    def detail(self):
        '''错误详情'''
        if self.msg:
            return self.msg

        if self.err:
            return str(self.err)

        return '未知的错误'


class VirtAPI(object):
    '''
    libvirt api包装
    '''
    def __init__(self):
        self.VirtError = VirtError

    def _host_alive(self, host_ipv4:str, times=3):
        '''
        检测宿主机是否可访问

        :param host_ipv4: 宿主机IP
        :param times:
        :return:
            True    # 可访问
            False   # 不可
        '''
        cmd = f'fping {host_ipv4} -r {times}'
        res, info = subprocess.getstatusoutput(cmd)
        if res == 0:
            return True
        return False

    def _get_connection(self, host_ip:str):
        '''
        建立与宿主机的连接

        :param host_ip: 宿主机IP
        :return:
            success: libvirt.virConnect
            failed: raise VirtError()

        :raise VirtError()
        '''
        if host_ip:
            if not self._host_alive(host_ip):
                raise VirtError(msg='宿主机连接失败')
            name = f'qemu+ssh://{host_ip}/system'
        else:
            name = 'qemu:///system'

        try:
            return libvirt.open(name=name)
        except libvirt.libvirtError as e:
            raise VirtError(err=e)

    def define(self, host_ipv4:str, xml_desc:str):
        '''
        在宿主机上创建一个虚拟机

        :param host_ipv4: 宿主机ip
        :param xml_desc: 定义虚拟机的xml
        :return:
            success: libvirt.virDomain()
            failed: raise VirtError()

        :raise VirtError()
        '''
        conn = self._get_connection(host_ipv4)
        try:
            dom = conn.defineXML(xml_desc)
            return dom
        except libvirt.libvirtError as e:
            raise VirtError(err=e)

    def get_domain(self, host_ipv4:str, vm_uuid:str):
        '''
        获取虚拟机

        :param host_ipv4: 宿主机IP
        :param vm_uuid: 虚拟机uuid
        :return:
            success: libvirt.virDomain()
            failed: raise VirtError()

        :raise VirtError()
        '''
        conn = self._get_connection(host_ipv4)
        try:
            return conn.lookupByUUIDString(vm_uuid)
        except libvirt.libvirtError as e:
            raise VirtError(err=e)

    def domain_exists(self, host_ipv4:str, vm_uuid:str):
        '''
        检测虚拟机是否已存在

        :param host_ipv4: 宿主机IP
        :param vm_uuid: 虚拟机uuid
        :return:
            True: 已存在
            False: 不存在

        :raise VirtError()
        '''
        conn = self._get_connection(host_ipv4)
        try:
            for d in conn.listAllDomains():
                if d.UUIDString() == vm_uuid:
                    return True
            return False
        except libvirt.libvirtError as e:
            raise VirtError(err=e)

    def undefine(self, host_ipv4:str, vm_uuid:str):
        '''
        删除一个虚拟机

        :param host_ipv4: 宿主机IP
        :param vm_uuid: 虚拟机uuid
        :return:
            success: True
            failed: False

        :raise VirtError()
        '''
        dom = self.get_domain(host_ipv4, vm_uuid)
        try:
            if dom.undefine() == 0:
                return True
            return False
        except libvirt.libvirtError as e:
            raise VirtError(msg=f'删除虚拟机失败,{str(e)}', err=e)

    def domain_status(self, host_ipv4:str, vm_uuid:str):
        '''
        获取虚拟机的当前状态

        :param host_ipv4: 宿主机IP
        :param vm_uuid: 虚拟机uuid
        :return:
            success: (state_code:int, state_str:str)

        :raise VirtError()
        '''
        domain = self.get_domain(host_ipv4, vm_uuid)
        code = self._status_code(domain)
        state_str = VM_STATE.get(code, 'no state')
        return (code, state_str)

    def _status_code(self, domain:libvirt.virDomain):
        '''
        获取虚拟机的当前状态码

        :param domain: 虚拟机实例
        :return:
            success: state_code:int

        :raise VirtError()
        '''
        try:
            info = domain.info()
            return info[0]
        except libvirt.libvirtError as e:
            raise VirtError(err=e)

    def is_shutoff(self, host_ipv4:str, vm_uuid:str):
        '''
        虚拟机是否关机状态

        :param host_ipv4: 宿主机IP
        :param vm_uuid: 虚拟机uuid
        :return:
            True: 关机
            False: 未关机

        :raise VirtError()
        '''
        domain = self.get_domain(host_ipv4=host_ipv4, vm_uuid=vm_uuid)
        return self._domain_is_shutoff(domain)

    def _domain_is_shutoff(self, domain:libvirt.virDomain):
        '''
        虚拟机是否关机状态

        :param domain: 虚拟机实例
        :return:
            True: 关机
            False: 未关机

        :raise VirtError()
        '''
        code = self._status_code(domain)
        return code == VIR_DOMAIN_SHUTOFF

    def is_running(self, host_ipv4:str, vm_uuid:str):
        '''
        虚拟机是否开机状态，阻塞、暂停、挂起都属于开启状态

        :param host_ipv4: 宿主机IP
        :param vm_uuid: 虚拟机uuid
        :return:
            True: 开机
            False: 未开机

        :raise VirtError()
        '''
        domain = self.get_domain(host_ipv4=host_ipv4, vm_uuid=vm_uuid)
        code = self._status_code(domain)
        if code in (VIR_DOMAIN_RUNNING, VIR_DOMAIN_BLOCKED, VIR_DOMAIN_PAUSED, VIR_DOMAIN_PMSUSPENDED):
            return True
        return False

    def _domain_is_running(self, domain:libvirt.virDomain):
        '''
        虚拟机是否开机状态，阻塞、暂停、挂起都属于开启状态

        :param domain: 虚拟机实例
        :return:
            True: 开机
            False: 未开机

        :raise VirtError()
        '''
        code = self._status_code(domain)
        if code in (VIR_DOMAIN_RUNNING, VIR_DOMAIN_BLOCKED, VIR_DOMAIN_PAUSED, VIR_DOMAIN_PMSUSPENDED):
            return True
        return False

    def start(self, host_ipv4:str, vm_uuid:str):
        '''
        开机启动一个虚拟机

        :param host_ipv4: 虚拟机所在的宿主机ip
        :param vm_uuid: 虚拟机uuid
        :return:
            success: True
            failed: False

        :raise VirtError()
        '''
        domain = self.get_domain(host_ipv4, vm_uuid)
        if self._domain_is_running(domain):
            return True

        try:
            res = domain.create()
            if res == 0:
                return True
            return False
        except libvirt.libvirtError as e:
            raise VirtError(msg=f'启动虚拟机失败,{str(e)}', err=e)

    def reboot(self, host_ipv4:str, vm_uuid:str):
        '''
        重启虚拟机

        :param host_ipv4: 虚拟机所在的宿主机ip
        :param vm_uuid: 虚拟机uuid
        :return:
            success: True
            failed: False

        :raise VirtError()
        '''
        domain = self.get_domain(host_ipv4, vm_uuid)
        if not self._domain_is_running(domain):
            return False

        try:
            res = domain.reboot()
            if res == 0:
                return True
            return False
        except libvirt.libvirtError as e:
            raise VirtError(msg=f'重启虚拟机失败, {str(e)}', err=e)

    def shutdown(self, host_ipv4:str, vm_uuid:str):
        '''
        关机

        :param host_ipv4: 虚拟机所在的宿主机ip
        :param vm_uuid: 虚拟机uuid
        :return:
            success: True
            failed: False

        :raise VirtError()
        '''
        domain = self.get_domain(host_ipv4, vm_uuid)
        if not self._domain_is_running(domain):
            return True

        try:
            res = domain.shutdown()
            if res == 0:
                return True
            return False
        except libvirt.libvirtError as e:
            raise VirtError(msg=f'关闭虚拟机失败, {str(e)}', err=e)

    def poweroff(self, host_ipv4:str, vm_uuid:str):
        '''
        关闭电源

        :param host_ipv4: 虚拟机所在的宿主机ip
        :param vm_uuid: 虚拟机uuid
        :return:
            success: True
            failed: False

        :raise VirtError()
        '''
        domain = self.get_domain(host_ipv4, vm_uuid)
        if not self._domain_is_running(domain):
            return True

        res = domain.destroy()
        try:
            if res == 0:
                return True
            return False
        except libvirt.libvirtError as e:
            raise VirtError(msg=f'关闭虚拟机电源失败, {str(e)}', err=e)

    def get_domain_xml_desc(self, host_ipv4:str, vm_uuid:str):
        '''
        动态从宿主机获取虚拟机的xml内容

        :param host_ipv4: 虚拟机所在的宿主机ip
        :param vm_uuid: 虚拟机uuid
        :return:
            xml: str    # success

        :raise VirtError()
        '''
        try:
            domain = self.get_domain(host_ipv4=host_ipv4, vm_uuid=vm_uuid)
            return domain.XMLDesc()
        except libvirt.libvirtError as e:
            raise VirtError(msg=str(e))


class VmDomain:
    """
    宿主机上虚拟机实例
    """
    def __init__(self, host_ip: str, vm_uuid: str):
        self._hip = host_ip
        self._vmid = vm_uuid
        self.virt = VirtAPI()

    def exists(self):
        """
        检测虚拟机是否已存在

        :return:
            True: 已存在
            False: 不存在

        :raise VirtError()
        """
        return self.virt.domain_exists(host_ipv4=self._hip, vm_uuid=self._vmid)

    def status(self):
        """
        获取虚拟机的当前运行状态

        :return:
            success: (state_code:int, state_str:str)

        :raise VirtError()
        """
        return self.virt.domain_status(host_ipv4=self._hip, vm_uuid=self._vmid)

    def undefine(self):
        """
        删除虚拟机

        :return:
            success: True
            failed: False

        :raise VirtError()
        """
        return self.virt.undefine(host_ipv4=self._hip, vm_uuid=self._vmid)

    def is_shutoff(self):
        """
        虚拟机是否关机状态

        :return:
            True: 关机
            False: 未关机

        :raise VirtError()
        """
        return self.virt.is_shutoff(host_ipv4=self._hip, vm_uuid=self._vmid)

    def is_running(self):
        """
        虚拟机是否开机状态，阻塞、暂停、挂起都属于开启状态

        :return:
            True: 开机
            False: 未开机

        :raise VirtError()
        """
        return self.virt.is_running(host_ipv4=self._hip, vm_uuid=self._vmid)

    def start(self):
        """
        开机启动虚拟机

        :return:
            success: True
            failed: False

        :raise VirtError()
        """
        return self.virt.start(host_ipv4=self._hip, vm_uuid=self._vmid)

    def reboot(self):
        """
        重启虚拟机

        :return:
            success: True
            failed: False

        :raise VirtError()
        """
        return self.virt.reboot(host_ipv4=self._hip, vm_uuid=self._vmid)

    def shutdown(self):
        """
        关机

        :return:
            success: True
            failed: False

        :raise VirtError()
        """
        return self.virt.shutdown(host_ipv4=self._hip, vm_uuid=self._vmid)

    def poweroff(self):
        """
        关闭电源

        :return:
            success: True
            failed: False

        :raise VirtError()
        """
        return self.virt.poweroff(host_ipv4=self._hip, vm_uuid=self._vmid)

    def xml_desc(self):
        """
        动态从宿主机获取虚拟机的xml内容

        :return:
            xml: str    # success

        :raise VirtError()
        """
        return self.virt.get_domain_xml_desc(host_ipv4=self._hip, vm_uuid=self._vmid)

    def attach_device(self, xml: str):
        """
        附加设备到虚拟机

        :param xml: 设备xml
        :return:
            True    # success
            False   # failed

        :raises: VirtError
        """
        domain = self.virt.get_domain(self._hip, self._vmid)
        try:
            ret = domain.attachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CONFIG)  # 指定将设备分配给持久化域
        except libvirt.libvirtError as e:
            msg = str(e)
            if 'already in the domain configuration' in msg:
                return True
            raise VirtError(msg=msg)
        if ret == 0:
            return True
        return False

    def detach_device(self, xml: str):
        """
        从虚拟机拆卸设备

        :param xml: 设备xml
        :return:
            True    # success
            False   # failed

        :raises: VirtError
        """
        domain = self.virt.get_domain(self._hip, self._vmid)
        try:
            ret = domain.detachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CONFIG)
        except libvirt.libvirtError as e:
            c = e.get_error_code()
            msg = e.get_error_message()
            if c and c == 99 and 'device not found' in msg:
                return True
            raise VirtError(msg=msg)
        if ret == 0:
            return True
        return False



