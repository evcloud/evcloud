import re
import sys
import traceback
from django.shortcuts import render


class Error(Exception):
    """
    错误定义
    """
    code = 500
    msg = 'error'
    err_code = 'Error'

    def __init__(self, code: int = 0, msg: str = '', err=None, err_code: str = ''):
        """
        :param code: 错误码
        :param msg: 错误信息
        :param err: 错误对象
        """
        self.code = code if code > 0 else self.code
        self.msg = msg if msg else self.msg
        self.err = err
        if err_code:
            self.err_code = err_code

    def __str__(self):
        return self.detail()

    def detail(self):
        """错误详情"""
        if self.msg:
            return self.msg

        if self.err:
            return str(self.err)

        return '未知的错误'

    def data(self, msg_key: str = None):
        if not msg_key:
            msg_key = 'code_text'

        return {
            'code': self.code,
            'err_code': self.err_code,
            msg_key: self.detail()
        }

    def render(self, request):
        class_path = (re.findall('\<class \'(.*?)\'>', str(type(self)))[0]).split('.')
        error_type = class_path[len(class_path) - 1]
        error_code = self.code
        error_tips = [self.msg]
        error_traceback = traceback.format_exc(limit=1, chain=self)
        return render(request, 'error.html',
                      context={'error_code': error_code, 'error_type': error_type,
                               'error_tips': error_tips, 'error_traceback': error_traceback},
                      status=500)

    @property
    def status_code(self):
        return self.code

    @classmethod
    def from_error(cls, err):
        """
        从其他错误生成当前错误对象

        :param err: 一个错误对象
        :return:
            object of Error or subclass
        """
        if not isinstance(err, Error):
            return cls(msg=str(err))

        return cls(msg=err.msg, code=err.code, err_code=err.err_code)


class SystemRunningError(Error):
    err_code = 'SystemRunningError'
    code = 500
    msg = '系统运行时错误.'

    def render(self, request):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        return render(request, 'error.html',
                      context={'error_code': self.code, 'error_type': 'SystemRunningError',
                               'error_tips': [self.msg, exc_value], 'error_traceback': traceback.format_exc(limit=1)},
                      status=500)


class AuthenticationFailedError(Error):
    err_code = 'AuthenticationFailed'
    code = 401
    msg = 'Incorrect authentication credentials.'


class NotAuthenticated(Error):
    err_code = 'NotAuthenticated'
    code = 401
    msg = 'Authentication credentials were not provided.'


class AccessDeniedError(Error):
    err_code = 'AccessDenied'
    code = 403
    msg = 'No access to the target resource'


class APIAccessDeniedError(AccessDeniedError):
    pass


class NotFoundError(Error):
    """
    网络错误类型定义
    """
    code = 404
    err_code = 'NotFound'
    msg = 'Target not found.'


class BadRequestError(Error):
    """
    请求错误类型定义
    """
    code = 400
    err_code = 'BadRequest'
    msg = 'bad request'


class InvalidParamError(BadRequestError):
    """
    参数无效错误类型定义
    """
    err_code = 'InvalidParam'
    msg = 'invalid param'


class VmError(Error):
    """
    虚拟机相关错误定义
    """
    pass


class VmNotExistError(VmError):
    err_code = 'VmNotExist'
    code = 404


class VmAccessDeniedError(VmError):
    err_code = 'VmAccessDenied'
    code = 403
    msg = 'No access to the vm resource'


class GroupAccessDeniedError(VmError):
    err_code = 'GroupAccessDenied'
    code = 403
    msg = "No access to the group's resource"


class VmRunningError(VmError):
    err_code = 'VmRunning'
    code = 409
    msg = 'vm is running, need shutdown it.'


class VmAlreadyExistError(VmError):
    err_code = 'VmAlreadyExist'
    code = 409
    msg = 'This virtual host already exists.'


class VmDiskImageMissError(VmError):
    err_code = 'VmDiskImageMiss'
    code = 409
    msg = 'The hard disk image for this virtual machine does not exist.'


class VmSysDiskSizeSmallError(VmError):
    err_code = 'VmSysDiskSizeSmall'
    code = 409
    msg = '系统盘容量太小.'


class AcrossGroupConflictError(VmError):
    err_code = 'AcrossGroupConflictError'
    code = 409
    msg = '资源冲突，不属于同一个宿主机组。'


class AcrossCenterConflictError(VmError):
    err_code = 'AcrossCenterConflict'
    code = 409
    msg = '资源冲突，不属于同一个数据中心。'


class VmTooManyVdiskMounted(VmError):
    err_code = 'TooManyVdiskMounted'
    code = 409
    msg = '不能挂载更多的硬盘了'


class Unsupported(Error):
    err_code = 'Unsupported'
    code = 409
    msg = '请求的操作不被支持'


class SnapNotExist(VmError):
    err_code = 'SnapNotExist'
    code = 404
    msg = '快照不存在'


class SnapNotBelongToVm(VmError):
    err_code = 'SnapNotBelongToVm'
    code = 409
    msg = '快照不属于指定虚拟主机'


class VPNError(Error):
    err_code = 'InternalServerError'


class NoSuchVPN(VPNError):
    code = 404
    msg = 'vpn账户不存在'
    err_code = 'NoSuchVPN'


class VPNAlreadyExists(VPNError):
    code = 400
    msg = 'vpn账户已存在'
    err_code = 'AlreadyExists'


class VdiskError(Error):
    """
    PCIe设备相关错误定义
    """
    pass


class VdiskInvalidParams(VdiskError):
    code = 400
    msg = '无效的参数'
    err_code = 'VdiskInvalidParams'


class VdiskAccessDenied(VdiskError):
    code = 403
    msg = '无资源访问权限'
    err_code = 'VdiskAccessDenied'


class VdiskNotExist(VdiskError):
    err_code = 'VdiskNotExist'
    code = 404
    msg = '云硬盘不存在'


class VdiskTooLarge(VdiskError):
    code = 409
    msg = '超出了可创建硬盘最大容量限制'
    err_code = 'VdiskTooLarge'


class VdiskNotEnoughQuota(VdiskError):
    code = 409
    msg = '没有足够的存储容量创建硬盘'
    err_code = 'VdiskNotEnoughQuota'


class VdiskAlreadyMounted(VdiskError):
    code = 409
    msg = '硬盘已被挂载'
    err_code = 'VdiskAlreadyMounted'


class VdiskNotActive(VdiskError):
    code = 409
    msg = '硬盘未激活使用'
    err_code = 'VdiskNotActive'


class NovncError(Error):
    pass


class NetworkError(Error):
    """
    网络错误类型定义
    """
    pass


class MacIpApplyFailed(NetworkError):
    code = 409
    msg = '申请mac ip资源失败'
    err_code = 'MacIpApplyFailed'


class ImageError(Error):
    """
    镜像相关错误类型定义
    """
    pass


class DeviceError(Error):
    """
    PCIe设备相关错误定义
    """
    pass


class DeviceAccessDenied(DeviceError):
    code = 403
    msg = '无资源访问权限'
    err_code = 'DeviceAccessDenied'


class DeviceNotFound(DeviceError):
    code = 404
    msg = '设备不存在'
    err_code = 'DeviceNotFound'


class DeviceNotActive(DeviceError):
    code = 409
    msg = '设备不可用'
    err_code = 'DeviceNotActive'


class ComputeError(Error):
    """
    计算资源相关错误定义
    """
    pass


class VcpuNotEnough(ComputeError):
    err_code = 'VcpuNotEnough'
    code = 409
    msg = 'vcpu资源不足'


class RamNotEnough(ComputeError):
    err_code = 'RamNotEnough'
    code = 409
    msg = '内存资源不足'


class ScheduleError(Error):
    pass


class NoMacIPError(ScheduleError):
    """没有mac ip资源可用"""
    code = 409
    msg = '没有可用的mac ip资源'
    err_code = 'NoMacIPAvailable'


class NoHostError(ScheduleError):
    """没有宿主机资源可用"""
    code = 409
    msg = '没有可用的宿主机资源'
    err_code = 'NoHostAvailable'


class NoHostOrMacIPError(ScheduleError):
    """没有宿主机或mac_ip资源可用"""
    code = 409
    msg = '没有可用的宿主机或者mac ip资源'
    err_code = 'NoHostOrMacIPAvailable'


class NoHostGroupError(Error):
    """没有宿主机组资源可用"""
    code = 409
    msg = '没有可用的宿主机资源'
    err_code = 'NoHostGroupAvailable'


class NoSuchImage(NotFoundError):
    msg = '没有此镜像'
    err_code = 'NoSuchImage'


class LocaldiskAlreadyMounted(VdiskError):
    code = 409
    msg = '本地硬盘已被挂载'
    err_code = 'LocaldiskAlreadyMounted'