import subprocess
import time

import libvirt
from xml.etree import ElementTree

from compute.managers import HostManager

VIR_DOMAIN_NOSTATE = 0  # no state
VIR_DOMAIN_RUNNING = 1  # the domain is running
VIR_DOMAIN_BLOCKED = 2  # the domain is blocked on resource
VIR_DOMAIN_PAUSED = 3  # the domain is paused by user
VIR_DOMAIN_SHUTDOWN = 4  # the domain is being shut down
VIR_DOMAIN_SHUTOFF = 5  # the domain is shut off
VIR_DOMAIN_CRASHED = 6  # the domain is crashed
VIR_DOMAIN_PMSUSPENDED = 7  # the domain is suspended by guest power management
# NB: this enum value will increase over time as new events are added to the
# libvirt API. It reflects the last state supported by this version of the libvirt API.
VIR_DOMAIN_LAST = 8
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


class VirErrorNumber:
    """
    libvirt api error code
    """
    VIR_ERR_OK = 0
    VIR_ERR_INTERNAL_ERROR = 1  # internal error
    VIR_ERR_NO_MEMORY = 2  # memory allocation failure
    VIR_ERR_NO_SUPPORT = 3  # no support for this function
    VIR_ERR_UNKNOWN_HOST = 4  # could not resolve hostname
    VIR_ERR_NO_CONNECT = 5  # can't connect to hypervisor
    VIR_ERR_INVALID_CONN = 6  # invalid connection object
    VIR_ERR_INVALID_DOMAIN = 7  # invalid domain object
    VIR_ERR_INVALID_ARG = 8  # invalid function argument
    VIR_ERR_OPERATION_FAILED = 9  # a command to hypervisor failed
    VIR_ERR_GET_FAILED = 10  # a HTTP GET command to failed
    VIR_ERR_POST_FAILED = 11  # a HTTP POST command to failed
    VIR_ERR_HTTP_ERROR = 12  # unexpected HTTP error code
    VIR_ERR_SEXPR_SERIAL = 13  # failure to serialize an S-Expr
    VIR_ERR_NO_XEN = 14  # could not open Xen hypervisor control
    VIR_ERR_XEN_CALL = 15  # failure doing an hypervisor call
    VIR_ERR_OS_TYPE = 16  # unknown OS type
    VIR_ERR_NO_KERNEL = 17  # missing kernel information
    VIR_ERR_NO_ROOT = 18  # missing root device information
    VIR_ERR_NO_SOURCE = 19  # missing source device information
    VIR_ERR_NO_TARGET = 20  # missing target device information
    VIR_ERR_NO_NAME = 21  # missing domain name information
    VIR_ERR_NO_OS = 22  # missing domain OS information
    VIR_ERR_NO_DEVICE = 23  # missing domain devices information
    VIR_ERR_NO_XENSTORE = 24  # could not open Xen Store control
    VIR_ERR_DRIVER_FULL = 25  # too many drivers registered
    VIR_ERR_CALL_FAILED = 26  # not supported by the drivers (DEPRECATED)
    VIR_ERR_XML_ERROR = 27  # an XML description is not well formed or broken
    VIR_ERR_DOM_EXIST = 28  # the domain already exist
    VIR_ERR_OPERATION_DENIED = 29  # operation forbidden on read-only connections
    VIR_ERR_OPEN_FAILED = 30  # failed to open a conf file
    VIR_ERR_READ_FAILED = 31  # failed to read a conf file
    VIR_ERR_PARSE_FAILED = 32  # failed to parse a conf file
    VIR_ERR_CONF_SYNTAX = 33  # failed to parse the syntax of a conf file
    VIR_ERR_WRITE_FAILED = 34  # failed to write a conf file
    VIR_ERR_XML_DETAIL = 35  # detail of an XML error
    VIR_ERR_INVALID_NETWORK = 36  # invalid network object
    VIR_ERR_NETWORK_EXIST = 37  # the network already exist
    VIR_ERR_SYSTEM_ERROR = 38  # general system call failure
    VIR_ERR_RPC = 39  # some sort of RPC error
    VIR_ERR_GNUTLS_ERROR = 40  # error from a GNUTLS call
    VIR_WAR_NO_NETWORK = 41  # failed to start network
    VIR_ERR_NO_DOMAIN = 42  # domain not found or unexpectedly disappeared
    VIR_ERR_NO_NETWORK = 43  # network not found
    VIR_ERR_INVALID_MAC = 44  # invalid MAC address
    VIR_ERR_AUTH_FAILED = 45  # authentication failed
    VIR_ERR_INVALID_STORAGE_POOL = 46  # invalid storage pool object
    VIR_ERR_INVALID_STORAGE_VOL = 47  # invalid storage vol object
    VIR_WAR_NO_STORAGE = 48  # failed to start storage
    VIR_ERR_NO_STORAGE_POOL = 49  # storage pool not found
    VIR_ERR_NO_STORAGE_VOL = 50  # storage volume not found
    VIR_WAR_NO_NODE = 51  # failed to start node driver
    VIR_ERR_INVALID_NODE_DEVICE = 52  # invalid node device object
    VIR_ERR_NO_NODE_DEVICE = 53  # node device not found
    VIR_ERR_NO_SECURITY_MODEL = 54  # security model not found
    VIR_ERR_OPERATION_INVALID = 55  # operation is not applicable at this time
    VIR_WAR_NO_INTERFACE = 56  # failed to start interface driver
    VIR_ERR_NO_INTERFACE = 57  # interface driver not running
    VIR_ERR_INVALID_INTERFACE = 58  # invalid interface object
    VIR_ERR_MULTIPLE_INTERFACES = 59  # more than one matching interface found
    VIR_WAR_NO_NWFILTER = 60  # failed to start nwfilter driver
    VIR_ERR_INVALID_NWFILTER = 61  # invalid nwfilter object
    VIR_ERR_NO_NWFILTER = 62  # nw filter pool not found
    VIR_ERR_BUILD_FIREWALL = 63  # nw filter pool not found
    VIR_WAR_NO_SECRET = 64  # failed to start secret storage
    VIR_ERR_INVALID_SECRET = 65  # invalid secret
    VIR_ERR_NO_SECRET = 66  # secret not found
    VIR_ERR_CONFIG_UNSUPPORTED = 67  # unsupported configuration construct
    VIR_ERR_OPERATION_TIMEOUT = 68  # timeout occurred during operation
    VIR_ERR_MIGRATE_PERSIST_FAILED = 69  # a migration worked, but making the VM persist on the dest host failed
    VIR_ERR_HOOK_SCRIPT_FAILED = 70  # a synchronous hook script failed
    VIR_ERR_INVALID_DOMAIN_SNAPSHOT = 71  # invalid domain snapshot
    VIR_ERR_NO_DOMAIN_SNAPSHOT = 72  # domain snapshot not found
    VIR_ERR_INVALID_STREAM = 73  # stream pointer not valid
    VIR_ERR_ARGUMENT_UNSUPPORTED = 74  # valid API use but unsupported by the given driver
    VIR_ERR_STORAGE_PROBE_FAILED = 75  # storage pool probe failed
    VIR_ERR_STORAGE_POOL_BUILT = 76  # storage pool already built
    VIR_ERR_SNAPSHOT_REVERT_RISKY = 77  # force was not requested for a risky domain snapshot revert
    VIR_ERR_OPERATION_ABORTED = 78  # operation on a domain was canceled/aborted by user
    VIR_ERR_AUTH_CANCELLED = 79  # authentication cancelled
    VIR_ERR_NO_DOMAIN_METADATA = 80  # The metadata is not present
    VIR_ERR_MIGRATE_UNSAFE = 81  # Migration is not safe
    VIR_ERR_OVERFLOW = 82  # integer overflow
    VIR_ERR_BLOCK_COPY_ACTIVE = 83  # action prevented by block copy job
    VIR_ERR_OPERATION_UNSUPPORTED = 84  # The requested operation is not supported
    VIR_ERR_SSH = 85  # error in ssh transport driver
    VIR_ERR_AGENT_UNRESPONSIVE = 86  # guest agent is unresponsive, not running or not usable
    VIR_ERR_RESOURCE_BUSY = 87  # resource is already in use
    VIR_ERR_ACCESS_DENIED = 88  # operation on the object/resource was denied
    VIR_ERR_DBUS_SERVICE = 89  # error from a dbus service
    VIR_ERR_STORAGE_VOL_EXIST = 90  # the storage vol already exists
    VIR_ERR_CPU_INCOMPATIBLE = 91  # given CPU is incompatible with host CPU
    VIR_ERR_XML_INVALID_SCHEMA = 92  # XML document doesn't validate against schema
    VIR_ERR_MIGRATE_FINISH_OK = 93  # Finish API succeeded but it is expected to return NULL
    VIR_ERR_AUTH_UNAVAILABLE = 94  # authentication unavailable
    VIR_ERR_NO_SERVER = 95  # Server was not found
    VIR_ERR_NO_CLIENT = 96  # Client was not found
    VIR_ERR_AGENT_UNSYNCED = 97  # guest agent replies with wrong id to guest-sync command (DEPRECATED)
    VIR_ERR_LIBSSH = 98  # error in libssh transport driver
    VIR_ERR_DEVICE_MISSING = 99  # fail to find the desired device
    VIR_ERR_INVALID_NWFILTER_BINDING = 100  # invalid nwfilter binding
    VIR_ERR_NO_NWFILTER_BINDING = 101  # no nwfilter binding
    VIR_ERR_INVALID_DOMAIN_CHECKPOINT = 102  # invalid domain checkpoint
    VIR_ERR_NO_DOMAIN_CHECKPOINT = 103  # domain checkpoint not found
    VIR_ERR_NO_DOMAIN_BACKUP = 104  # domain backup job id not found
    VIR_ERR_INVALID_NETWORK_PORT = 105  # invalid network port object
    VIR_ERR_NETWORK_PORT_EXIST = 106  # the network port already exist
    VIR_ERR_NO_NETWORK_PORT = 107  # network port not found
    VIR_ERR_NO_HOSTNAME = 108  # no domain's hostname found
    VIR_ERR_NUMBER_LAST = 109


class VirtError(Exception):
    """
    libvirt函数封装错误类型定义
    """
    def __init__(self, code: int = 0, msg: str = '', err=None):
        """
        :param code: 错误码
        :param msg: 错误信息
        :param err: 错误对象
        """
        self.code = code
        self.msg = msg
        self.err = err

    def __str__(self):
        return self.detail()

    def detail(self):
        """错误详情"""
        if self.msg:
            return self.msg

        if self.err:
            return str(self.err)

        return '未知的错误'


class VirDomainNotExist(VirtError):
    """虚拟机不存在"""
    pass


class VirHostDown(VirtError):
    """无法连接宿主机"""
    pass


def wrap_error(err: libvirt.libvirtError, msg=''):
    err_code = err.get_error_code()
    msg = msg if msg else str(err)
    if err_code == VirErrorNumber.VIR_ERR_NO_DOMAIN:
        return VirDomainNotExist(code=err_code, msg=msg, err=err)

    return VirtError(code=err_code, msg=msg, err=err)


class VirtHost:
    VirtError = VirtError

    def __init__(self, host_ipv4: str):
        self.host_ipv4 = host_ipv4
        self.ssh_host = HostManager().get_host_by_ipv4(host_ipv4=self.host_ipv4)

        self.ssh_key = self.ssh_host.group.center.ssh_key
        self._conn = None

    def __del__(self):
        self.close()

    def close(self):
        if isinstance(self._conn, libvirt.virConnect) or hasattr(self._conn, 'close'):
            self._conn.close()

    def host_alive(self, times=3, timeout=3):
        """
        检测宿主机是否可访问

        :param times: ping次数
        :param timeout:
        :return:
            True    # 可访问
            False   # 不可
        """
        cmd = f'ping -c {times} -i 0.1 -W {timeout} {self.host_ipv4}'
        res, info = subprocess.getstatusoutput(cmd)
        if res == 0:
            return True

        return False

    def open_connection(self):
        """
        建立一个新的与宿主机的连接

        :return:
            success: libvirt.virConnect
            failed: raise VirtError()

        :raise VirtError(), VirHostDown()
        """
        host_ip = self.host_ipv4
        if host_ip:
            if not self.host_alive() or not self.ssh_key:
                raise VirHostDown(msg='无法访问宿主机')
            name = f'qemu+ssh://{host_ip}/system?no_tty=1&keyfile={self.ssh_key}'      # no_tty如果设置为非零值，如果它无法自动登录到远程计算机，它将阻止ssh询问密码
        else:
            name = 'qemu:///system'

        try:
            return libvirt.open(name=name)
        except libvirt.libvirtError as e:
            raise wrap_error(err=e, msg=f'连接宿主机错误, 请确认宿主机是否配置ssh密钥,{str(e)}')

    def get_connection(self):
        """
        :raise VirtError(), VirHostDown()
        """
        if self._conn is None:
            self._conn = self.open_connection()

        return self._conn

    @property
    def connection(self):
        return self.get_connection()

    def define(self, xml_desc: str):
        """
        在宿主机上创建一个虚拟机

        :param xml_desc: 定义虚拟机的xml
        :return:
            success: libvirt.virDomain()
            failed: raise VirtError()

        :raise VirtError()
        """
        conn = self.get_connection()
        try:
            dom = conn.defineXML(xml_desc)
            return dom
        except libvirt.libvirtError as e:
            raise wrap_error(err=e)

    def get_domain(self, vm_uuid: str):
        """
        获取虚拟机

        :param vm_uuid: 虚拟机uuid
        :return:
            success: libvirt.virDomain()
            failed: raise VirtError()

        :raise VirtError(), VirDomainNotExist(), VirHostDown()
        """
        conn = self.get_connection()
        try:
            return conn.lookupByUUIDString(vm_uuid)
        except libvirt.libvirtError as e:
            raise wrap_error(err=e)

    def domain_exists(self, vm_uuid: str):
        """
        检测虚拟机是否已存在

        :param vm_uuid: 虚拟机uuid
        :return:
            True: 已存在
            False: 不存在

        :raise VirtError()
        """
        try:
            self.get_domain(vm_uuid)
        except VirDomainNotExist as e:
            return False

        return True

    def undefine(self, vm_uuid: str):
        """
        删除一个虚拟机

        :param vm_uuid: 虚拟机uuid
        :return:
            success: True
            failed: False

        :raise VirtError()
        """
        try:
            dom = self.get_domain(vm_uuid)
        except VirDomainNotExist as e:
            return True

        try:
            dom.destroy()  # 确保vm关闭才能删除掉
        except libvirt.libvirtError as e:
            pass

        try:
            # ok = dom.undefine()
            # 当存在NVRAM文件时，删除虚拟机需增加--nvram参数；若不存在NVRAM文件，经测试也可删除
            ok = dom.undefineFlags(libvirt.VIR_DOMAIN_UNDEFINE_NVRAM)
            if ok == 0:
                return True
            return False
        except libvirt.libvirtError as e:
            err = wrap_error(err=e, msg=f'删除虚拟机失败,{str(e)}')
            if isinstance(err, VirDomainNotExist):
                return True

            raise err

    def domain_status(self, vm_uuid: str):
        """
        获取虚拟机的当前状态

        :param vm_uuid: 虚拟机uuid
        :return:
            success: (state_code:int, state_str:str)

        :raise VirtError()
        """
        try:
            domain = self.get_domain(vm_uuid)
        except VirDomainNotExist as e:
            return VIR_DOMAIN_MISS, VM_STATE.get(VIR_DOMAIN_MISS, 'miss')
        except VirHostDown as e:
            return VIR_DOMAIN_HOST_DOWN, VM_STATE.get(VIR_DOMAIN_HOST_DOWN, 'host connect failed')

        code = self.status_code(domain)
        state_str = VM_STATE.get(code, 'no state')
        return code, state_str

    @staticmethod
    def status_code(domain: libvirt.virDomain):
        """
        获取虚拟机的当前状态码

        :param domain: 虚拟机实例
        :return:
            success: state_code:int

        :raise VirtError()
        """
        try:
            info = domain.info()
            return info[0]
        except libvirt.libvirtError as e:
            raise wrap_error(err=e)

    def is_shutoff(self, vm_uuid: str):
        """
        虚拟机是否关机状态

        :param vm_uuid: 虚拟机uuid
        :return:
            True: 关机
            False: 未关机

        :raise VirtError()
        """
        domain = self.get_domain(vm_uuid=vm_uuid)
        return self.domain_is_shutoff(domain)

    def domain_is_shutoff(self, domain: libvirt.virDomain):
        """
        虚拟机是否关机状态

        :param domain: 虚拟机实例
        :return:
            True: 关机
            False: 未关机

        :raise VirtError()
        """
        code = self.status_code(domain)
        return code == VIR_DOMAIN_SHUTOFF

    def is_running(self, vm_uuid: str):
        """
        虚拟机是否开机状态，阻塞、暂停、挂起都属于开启状态

        :param vm_uuid: 虚拟机uuid
        :return:
            True: 开机
            False: 未开机

        :raise VirtError()
        """
        domain = self.get_domain(vm_uuid=vm_uuid)
        code = self.status_code(domain)
        if code in (VIR_DOMAIN_RUNNING, VIR_DOMAIN_BLOCKED, VIR_DOMAIN_PAUSED, VIR_DOMAIN_PMSUSPENDED):
            return True

        return False

    def domain_is_running(self, domain: libvirt.virDomain):
        """
        虚拟机是否开机状态，阻塞、暂停、挂起都属于开启状态

        :param domain: 虚拟机实例
        :return:
            True: 开机
            False: 未开机

        :raise VirtError()
        """
        code = self.status_code(domain)
        if code in (VIR_DOMAIN_RUNNING, VIR_DOMAIN_BLOCKED, VIR_DOMAIN_PAUSED, VIR_DOMAIN_PMSUSPENDED):
            return True
        return False

    def start(self, vm_uuid: str):
        """
        开机启动一个虚拟机

        :param vm_uuid: 虚拟机uuid
        :return:
            success: True
            failed: False

        :raise VirtError()
        """
        domain = self.get_domain(vm_uuid)
        return self.start_domain(domain)

    def start_domain(self, domain: libvirt.virDomain):
        """
        开机启动一个虚拟机

        :return:
            success: True
            failed: False

        :raise VirtError()
        """
        if self.domain_is_running(domain):
            return True

        try:
            res = domain.create()
            if res == 0:
                return True
            return False
        except libvirt.libvirtError as e:
            raise wrap_error(err=e, msg=f'启动虚拟机失败,{str(e)}')

    def reboot(self, vm_uuid: str):
        """
        重启虚拟机

        :param vm_uuid: 虚拟机uuid
        :return:
            success: True
            failed: False

        :raise VirtError()
        """
        domain = self.get_domain(vm_uuid)
        return self.reboot_domain(domain)

    def reboot_domain(self, domain: libvirt.virDomain):
        """
        重启虚拟机

        :return:
            success: True
            failed: False

        :raise VirtError()
        """
        if not self.domain_is_running(domain):
            return False

        try:
            res = domain.reboot()
            if res == 0:
                return True
            return False
        except libvirt.libvirtError as e:
            raise wrap_error(err=e, msg=f'重启虚拟机失败, {str(e)}')

    def shutdown(self, vm_uuid: str):
        """
        关机

        :param vm_uuid: 虚拟机uuid
        :return:
            success: True
            failed: False

        :raise VirtError()
        """
        domain = self.get_domain(vm_uuid)
        return self.shutdown_domain(domain)

    def shutdown_domain(self, domain: libvirt.virDomain):
        """
        关机

        :return:
            success: True
            failed: False

        :raise VirtError()
        """
        if not self.domain_is_running(domain):
            return True

        try:
            res = domain.shutdown()
            if res == 0:
                return True
            return False
        except libvirt.libvirtError as e:
            raise wrap_error(err=e, msg=f'关闭虚拟机失败, {str(e)}')

    def poweroff(self, vm_uuid: str):
        """
        关闭电源

        :param vm_uuid: 虚拟机uuid
        :return:
            success: True
            failed: False

        :raise VirtError()
        """
        domain = self.get_domain(vm_uuid)
        return self.power_off_domain(domain)

    def power_off_domain(self, domain: libvirt.virDomain):
        """
        关闭电源

        :return:
            success: True
            failed: False

        :raise VirtError()
        """
        if not self.domain_is_running(domain):
            return True

        res = domain.destroy()
        try:
            if res == 0:
                return True
            return False
        except libvirt.libvirtError as e:
            raise wrap_error(err=e, msg=f'关闭虚拟机电源失败, {str(e)}')

    def get_domain_xml_desc(self, vm_uuid: str):
        """
        动态从宿主机获取虚拟机的xml内容

        :param vm_uuid: 虚拟机uuid
        :return:
            xml: str    # success

        :raise VirtError()
        """
        try:
            domain = self.get_domain(vm_uuid=vm_uuid)
            return domain.XMLDesc()
        except libvirt.libvirtError as e:
            raise wrap_error(err=e)

    def list_storage_pools(self):
        c = self.get_connection()
        r = c.listAllStoragePools()
        return r

    def list_all_devices(self):
        c = self.get_connection()
        r = c.listAllDevices()
        return r

    def list_all_networks(self):
        c = self.connection
        r = c.listAllNetworks()
        return r

    def get_max_vcpus(self) -> int:
        c = self.connection
        return c.getMaxVcpus(type='kvm')

    def get_info(self):
        c = self.connection
        return c.getInfo()

    def get_hugepages(self):
        """获取大页内存"""

        ip = f'{self.host_ipv4}'
        key = f'{self.ssh_key}'

        line = ['ssh', '-i', key, ip, 'cat /proc/meminfo  | grep -E "HugePages_Total|HugePages_Free"']

        try:
            p = subprocess.check_output(line, stderr=subprocess.STDOUT, timeout=5)
        except subprocess.TimeoutExpired as time_e:
            raise ValueError(f'{time_e}')
        except subprocess.CalledProcessError as call_e:
            raise ValueError(f'{call_e.output.decode(encoding="utf-8")}')

        p = p.decode(encoding="utf-8").split('\n')

        d = {}
        for i in p:
            if not i:
                break
            men = i.split(':      ')   # ['HugePages_Total', ' 0'] ['HugePages_Free', '  0']
            d[men[0]] = men[1].strip()

        return d

    def get_defined_domain_num(self) -> int:
        """
        宿主机已创建vm的数量

        :raises: VirtError
        """
        conn = self.connection
        try:
            num = conn.numOfDefinedDomains()
        except libvirt.libvirtError as e:
            raise wrap_error(err=e)

        return num


class VmStatsRecord:
    """
    Tracks a set of VM stats for a single timestamp
    """
    def __init__(self, timestamp,
                 cpu_time_abs,
                 host_cpus, guest_cpus,
                 total_mem_kb, cur_mem_kb,
                 disk_rd_bytes, disk_wr_bytes,
                 net_rx_bytes, net_tx_bytes):
        self.timestamp = timestamp
        self.cpu_time_abs = cpu_time_abs
        self.host_cpus = host_cpus
        self.guest_cpus = guest_cpus
        self.total_mem_kb = total_mem_kb
        self.cur_mem_kb = cur_mem_kb
        self.disk_rd_kb = disk_rd_bytes // 1024
        self.disk_wr_kb = disk_wr_bytes // 1024
        self.net_rx_kb = net_rx_bytes // 1024
        self.net_tx_kb = net_tx_bytes // 1024
        self._curr_mem_percent = 0

    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'cpu_time_abs': self.cpu_time_abs,
            'host_cpus': self.host_cpus,
            'guest_cpus': self.guest_cpus,
            'total_mem_kb': self.total_mem_kb,
            'cur_mem_kb': self.cur_mem_kb,
            'disk_rd_kb': self.disk_rd_kb,
            'disk_wr_kb': self.disk_wr_kb,
            'net_tx_kb': self.net_tx_kb,
            'net_rx_kb': self.net_rx_kb,
            'curr_mem_percent': self.curr_mem_percent
        }

    @property
    def curr_mem_percent(self):
        if self._curr_mem_percent == 0:
            if self.total_mem_kb > 0:
                curr_mem_percent = (self.cur_mem_kb / float(self.total_mem_kb)) * 100
                self._curr_mem_percent = max(0.0, min(curr_mem_percent, 100.0))

        return self._curr_mem_percent


class VmDomain:
    """
    宿主机上虚拟机实例
    """
    def __init__(self, host_ip: str, vm_uuid: str):
        self._hip = host_ip
        self._vm_uuid = vm_uuid
        self._host = None
        self._domain = None

    def __getattr__(self, attr):
        """
        If an attribute does not exist on this instance, then we also attempt
        to proxy it to the libvirt.virDomain  object.
        """
        try:
            return getattr(self.domain, attr)
        except AttributeError:
            return self.__getattribute__(attr)

    def is_same_host(self, host_ipv4: str):
        """
        是否同一个宿主机
        """
        return self._hip == host_ipv4

    def is_same_domain(self, host_ipv4: str, vm_uuid: str):
        """
        是否同一个宿主机
        """
        return (self._hip == host_ipv4) and (self._vm_uuid == vm_uuid)

    @property
    def host(self):
        if self._host is None:
            self._host = VirtHost(host_ipv4=self._hip)

        return self._host

    @property
    def domain(self):
        """
        :raise VirtError(), VirDomainNotExist(), VirHostDown()
        """
        if self._domain is None:
            self._domain = self.host.get_domain(self._vm_uuid)

        return self._domain

    @domain.setter
    def domain(self, domain: libvirt.virDomain):
        self._domain = domain

    def exists(self):
        """
        检测虚拟机是否已存在

        :return:
            True: 已存在
            False: 不存在

        :raise VirtError()
        """
        return self.host.domain_exists(vm_uuid=self._vm_uuid)

    def status(self):
        """
        获取虚拟机的当前运行状态

        :return:
            success: (state_code:int, state_str:str)

        :raise VirtError()
        """
        try:
            domain = self.domain
        except VirDomainNotExist as e:
            return VIR_DOMAIN_MISS, VM_STATE.get(VIR_DOMAIN_MISS, 'miss')
        except VirHostDown as e:
            return VIR_DOMAIN_HOST_DOWN, VM_STATE.get(VIR_DOMAIN_HOST_DOWN, 'host connect failed')

        code = self.host.status_code(domain)
        state_str = VM_STATE.get(code, 'no state')
        return code, state_str

    @staticmethod
    def get_hex_uuid_from_domain(domain: libvirt.virDomain):
        vm_uuid = domain.UUIDString()
        vm_uuid = vm_uuid.replace('-', '')
        return vm_uuid

    @classmethod
    def define(cls, host_ipv4: str, xml_desc: str):
        """
        :raise VirtError()
        """
        host = VirtHost(host_ipv4)
        domain = host.define(xml_desc)
        vm_uuid = cls.get_hex_uuid_from_domain(domain)
        vm_domain = cls(host_ip=host_ipv4, vm_uuid=vm_uuid)
        vm_domain._host = host
        vm_domain.domain = domain
        return vm_domain

    def undefine(self):
        """
        删除虚拟机

        :return:
            success: True
            failed: False

        :raise VirtError()
        """
        ok = self.host.undefine(vm_uuid=self._vm_uuid)
        if ok:
            self.domain = None

        return ok

    def is_shutoff(self):
        """
        虚拟机是否关机状态

        :return:
            True: 关机
            False: 未关机

        :raise VirtError()
        """
        return self.host.domain_is_shutoff(self.domain)

    def is_running(self):
        """
        虚拟机是否开机状态，阻塞、暂停、挂起都属于开启状态

        :return:
            True: 开机
            False: 未开机
            None: vm miss

        :raise VirtError()
        """
        return self.host.domain_is_running(self.domain)

    def start(self):
        """
        开机启动虚拟机

        :return:
            success: True
            failed: False

        :raise VirtError()
        """
        return self.host.start_domain(self.domain)

    def reboot(self):
        """
        重启虚拟机

        :return:
            success: True
            failed: False

        :raise VirtError()
        """
        return self.host.reboot_domain(self.domain)

    def shutdown(self):
        """
        关机

        :return:
            success: True
            failed: False

        :raise VirtError()
        """
        return self.host.shutdown_domain(self.domain)

    def poweroff(self):
        """
        关闭电源

        :return:
            success: True
            failed: False

        :raise VirtError()
        """
        return self.host.power_off_domain(self.domain)

    def xml_desc(self, inactive: bool = False):
        """
        动态从宿主机获取虚拟机的xml内容

        :param inactive: True(获取非活动的持久域的xml)，False(获取当前运行域的xml)
        :return:
            xml: str    # success

        :raise VirtError()
        """
        try:
            if inactive:
                return self.domain.XMLDesc(libvirt.VIR_DOMAIN_XML_INACTIVE)

            return self.domain.XMLDesc()
        except libvirt.libvirtError as e:
            raise wrap_error(err=e)

    def attach_device(self, xml: str):
        """
        插设备到虚拟机，支持热插拔

        :param xml: 设备xml
        :return:
            True    # success
            False   # failed

        :raises: VirtError
        """
        active = self.is_running()
        if not active:
            return self.attach_device_persisted(xml)    # 持久化域

        ok = self.attach_device_hotplug(xml)
        if not ok:
            return False

        err = None
        try:
            ok = self.attach_device_persisted(xml)       # 持久化域
            if ok:
                return True
        except VirtError as e:
            err = e

        # 恢复活动域
        try:
            self.detach_device_hotplug(xml)
        except VirtError:
            pass

        if err is not None:
            raise err

        return False

    def attach_device_persisted(self, xml: str):
        """
        冷插设备到虚拟机持久化域

        :param xml: 设备xml
        :return:
            True    # success
            False   # failed

        :raises: VirtError
        """
        domain = self.domain
        try:
            ret = domain.attachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CONFIG)  # 指定将设备分配给持久化域
        except libvirt.libvirtError as e:
            msg = e.get_error_message()
            raise wrap_error(err=e, msg=msg)

        if ret == 0:
            return True

        return False

    def attach_device_hotplug(self, xml: str):
        """
        热插拔设备到虚拟机活动域

        :param xml: 设备xml
        :return:
            True    # success
            False   # failed

        :raises: VirtError
        """
        domain = self.domain
        try:
            ret = domain.attachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_LIVE)  # 指定将设备分配给活动域
        except libvirt.libvirtError as e:
            msg = e.get_error_message()
            raise wrap_error(err=e, msg=msg)

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
        active = self.is_running()
        ok = self.detach_device_persisted(xml)      # 从持久化域移除
        if not ok:
            return False

        if not active:
            return True

        # 如果虚拟机是活动的，从活动域移除
        err = None
        try:
            ok = self.detach_device_hotplug(xml)
            if ok:
                return True
        except VirtError as e:
            err = e

        # 恢复持久化域
        try:
            self.attach_device_persisted(xml)
        except VirtError:
            pass

        if err is not None:
            raise err

        return False

    def detach_device_hotplug(self, xml: str):
        """
        从虚拟机热插拔拆卸设备，只影响当前活动虚拟机域

        :param xml: 设备xml
        :return:
            True    # success
            False   # failed

        :raises: VirtError
        """
        domain = self.domain
        try:
            ret = domain.detachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_LIVE)     # 活动的虚拟机域
        except libvirt.libvirtError as e:
            msg = e.get_error_message()
            # c = e.get_error_code()
            # if c == VirErrorNumber.VIR_ERR_OPERATION_FAILED and 'not found' in msg.lower():
            #     return True

            raise wrap_error(err=e, msg=msg)
        if ret == 0:
            return True

        return False

    def detach_device_persisted(self, xml: str):
        """
        从虚拟机持久化域拆卸设备

        :param xml: 设备xml
        :return:
            True    # success
            False   # failed

        :raises: VirtError
        """
        domain = self.domain
        try:
            ret = domain.detachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_CONFIG)   # 虚拟机持久化域
        except libvirt.libvirtError as e:
            c = e.get_error_code()
            msg = e.get_error_message()
            if c and c == VirErrorNumber.VIR_ERR_DEVICE_MISSING:
                return True

            raise wrap_error(err=e, msg=msg)

        if ret == 0:
            return True

        return False

    def set_user_password(self, username: str, password: str):
        """
        修改虚拟主机登录用户密码

        :param username: 用户名
        :param password: 新密码
        :return:
            True
            False

        :raises: VirtError
        """
        domain = self.domain
        try:
            ret = domain.setUserPassword(user=username, password=password)
        except libvirt.libvirtError as e:
            raise wrap_error(err=e)
        if ret == 0:
            return True
        return False

    def live_migrate(self, dest_host_conn, undefine_source: bool = True):
        """
        :raise VirtError(), VirHostDown()
        """
        flags = libvirt.VIR_MIGRATE_LIVE | libvirt.VIR_MIGRATE_PERSIST_DEST
        if undefine_source:
            flags |= libvirt.VIR_MIGRATE_UNDEFINE_SOURCE

        src_domain = self.domain
        try:
            params = {}
            d_xml = src_domain.XMLDesc()
            params[libvirt.VIR_MIGRATE_PARAM_DEST_XML] = d_xml
            domain = src_domain.migrate3(dconn=dest_host_conn, params=params, flags=flags)
        except libvirt.libvirtError as e:
            raise wrap_error(err=e)

        self.domain = domain
        return domain

    def get_stats(self):
        """
        :raises: VirtError
        """
        if self.is_shutoff():
            pass

        # vm memory
        total_mem_kb, cur_mem_kb = self._mem_stats()

        # vm network
        net_rx_bytes, net_tx_bytes = self._net_io_stats()

        # vm cpu
        disk_rx_bytes, disk_wr_bytes = self._disk_io_stats()

        # vm cpu
        host_cpus, guest_cpus, cpu_time_abs, timestamp = self._cpu_stats()

        return VmStatsRecord(
            timestamp=timestamp,
            cpu_time_abs=cpu_time_abs,
            host_cpus=host_cpus,
            guest_cpus=guest_cpus,
            disk_rd_bytes=disk_rx_bytes,
            disk_wr_bytes=disk_wr_bytes,
            net_rx_bytes=net_rx_bytes,
            net_tx_bytes=net_tx_bytes,
            cur_mem_kb=cur_mem_kb,
            total_mem_kb=total_mem_kb
        )

    def _cpu_stats(self):
        host_cpus = 0
        guest_cpus = 0
        cpu_time_abs = 0
        timestamp = time.time()
        try:
            host_info = self.host.get_connection().getInfo()
            host_cpus = host_info[2]        # host_active_processor_count

            info = self.domain.info()
            state = info[0]
            guest_cpus = info[3]
            cpu_time_abs = info[4]
            if state in [libvirt.VIR_DOMAIN_SHUTOFF, libvirt.VIR_DOMAIN_CRASHED]:  # offline
                return host_cpus, 0, 0, timestamp
        except Exception as e:
            pass

        return host_cpus, guest_cpus, cpu_time_abs, timestamp

    def _disk_io_stats(self):
        rd_bytes = 0
        wr_bytes = 0
        domain = self.domain
        if not domain.isActive():
            return 0, 0

        tree = ElementTree.fromstring(domain.XMLDesc())
        devices = tree.findall('devices/disk/target')
        for d in devices:
            device = d.get('dev')

            try:
                io = domain.blockStats(device)
                if io:
                    rd_bytes += io[1]
                    wr_bytes += io[3]
            except libvirt.libvirtError:
                pass

        return rd_bytes, wr_bytes

    def _net_io_stats(self) -> (int, int):
        """
        :return:
            (rx: int    # The number of bytes received by network io.
            tx: int)    # The number of bytes transmitted by the network io.
        """
        rx_bytes = 0
        tx_bytes = 0

        try:
            domain = self.domain
            if not domain.isActive():
                return 0, 0

            vm_xml = self.domain.XMLDesc()
            tree = ElementTree.fromstring(vm_xml)
            interfaces = tree.findall('devices/interface/target')
            for i in interfaces:
                dev = i.get('dev')
                try:
                    io_info = self.domain.interfaceStats(dev)
                    if io_info:
                        rx_bytes += io_info[0]
                        tx_bytes += io_info[4]
                except libvirt.libvirtError as err:
                    pass
        except Exception as e:
            pass

        return rx_bytes, tx_bytes

    def _mem_stats(self):
        total_mem_kb = 1
        cur_mem_kb = 0
        try:
            self.domain.setMemoryStatsPeriod(5)
            stats = self.domain.memoryStats()
            total_mem_kb = stats.get("actual", 1)
            cur_mem_kb = max(0, total_mem_kb - stats.get("unused", total_mem_kb))
        except libvirt.libvirtError as err:
            pass

        return total_mem_kb, cur_mem_kb


class VmStoragePool:
    """
    存储池
    """
    def __init__(self, conn: libvirt.virConnect, name):
        self._conn = conn
        self.name = name
        self._pool = None

    def _get_pool(self):
        if not self._pool:
            try:
                self._pool = self._conn.storagePoolLookupByName(self.name)
            except libvirt.libvirtError as e:
                raise VirtError(msg=str(e))

        return self._pool

    def create_volume(self, volume_name, volume_capacity, drive=None):
        """
        创建一个存储卷

        :param volume_name: 卷名称
        :param volume_capacity: 容量大小，单位GB
        :param drive: 卷格式
        :return:
            libvirt.virStorageVol()

        :raises: VirtError
        """
        if drive is None:
            drive = 'qcow2'

        volume_xml = """
            <volume>
                <name>{volume_name}</name>
                <allocation>0</allocation>
                <capacity unit="G">{volume_capacity}</capacity>
                <target> 
                    <format type="{drive}"/> 
                </target>                             
            </volume>
        """
        volume_xml = volume_xml.format(volume_name=volume_name, volume_capacity=volume_capacity, drive=drive)
        try:
            pool = self._get_pool()
            return pool.createXML(volume_xml, 0)
        except libvirt.libvirtError as e:
            raise wrap_error(err=e, msg=f'创建存储卷失败，失败原因：{str(e)}')

    def delete_volume(self, volume_name):
        """
        删除存储卷
        :param volume_name: 卷名称
        :return:
            True

        :raises: VirtError
        """
        try:
            pool = self._get_pool()
            volume = pool.storageVolLookupByName(volume_name)
            r = volume.delete(0)  # volume.delete(0)从存储池里面删除,volume.wipe(0),从磁盘删除
            if r == 0:
                return True
            raise VirtError(msg='删除失败')
        except libvirt.libvirtError as e:
            raise wrap_error(err=e)

    def list_volumes(self):
        pool = self._get_pool()
        return pool.listAllVolumes()
