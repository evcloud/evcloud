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

    def data(self, msg_key: str = 'code_text'):
        return {
            'code': self.code,
            'err_code': self.err_code,
            msg_key: self.detail()
        }

    @property
    def status_code(self):
        return self.code


class AccessDeniedError(Error):
    err_code = 'AccessDenied'
    code = 403
    msg = 'No access to the target resource'


class NotFoundError(Error):
    """
    网络错误类型定义
    """
    code = 404
    err_code = 'NotFound'
    msg = 'Target not found.'


class BadRequestError(Error):
    """
    网络错误类型定义
    """
    code = 400
    err_code = 'BadRequest'
    msg = 'bad request'


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


class AcrossGroupConflictError(VmError):
    err_code = 'AcrossGroupConflictError'
    code = 409
    msg = '资源冲突，不属于同一个宿主机组。'


class VPNError(Error):
    pass


class VdiskError(Error):
    """
    PCIe设备相关错误定义
    """
    pass


class NovncError(Error):
    pass


class NetworkError(Error):
    """
    网络错误类型定义
    """
    pass


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


class ComputeError(Error):
    """
    计算资源相关错误定义
    """
    pass
