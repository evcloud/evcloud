#coding=utf-8

ERR_AUTH_NO_LOGIN       = '40001'
ERR_AUTH_LOGIN          = '40002'
ERR_AUTH_LOGOUT         = '40003'
ERR_AUTH_PERM           = '40004'
ERR_GROUP_ID            = '40005'
ERR_HOST_ID             = '40006'
ERR_IMAGE_ID            = '40007'
ERR_CEPH_ID             = '40008'
ERR_VLAN_ID             = '40009'
ERR_VM_UUID             = '40010'
ERR_VM_NO_OP            = '40011'
ERR_ARGS_VM_VCPU        = '40012'
ERR_ARGS_VM_MEM         = '40013'
ERR_ARGS_VM_EDIT_NONE   = '40014'
ERR_ARGS_REQUIRED       = '40015'
ERR_ARGS_VM_CREATE_NO_VLANTYPE = '40016'
ERR_DISK_NAME           = '40017'
ERR_CENTER_ID           = '40018'
ERR_VM_NAME             = '40019'
ERR_VLAN_TYPE_ID        = '40020'
ERR_VLAN_FILTER_NONE    = '40021'
ERR_HOST_FILTER_NONE    = '40022'
ERR_VM_MIGRATE_DIFF_CEPH= '40023'
ERR_VM_MIGRATE_LIVING   = '40024'
ERR_HOST_CLAIM          = '40035'
ERR_VM_RESET_LIVING     = '40036'
ERR_VM_EDIT_LIVING      = '40037'

ERR_ARGS_DECORATOR      = '50001'
ERR_PROCESS             = '50002'
ERR_LOG                 = '50003'
ERR_VLAN_NO_FIND        = '50004'
ERR_VM_DEFINE           = '50005'
ERR_VM_OP               = '50006'
ERR_VM_EDIT_REMARKS     = '50007'
ERR_VM_EDIT             = '50008'
ERR_VM_MIGRATE          = '50009'
ERR_DISK_INIT           = '50010'
ERR_DISK_ARCHIVE        = '50011'
ERR_IMAGE_INFO          = '50013' 
ERR_IMAGE_CEPHHOST      = '50014'
ERR_IMAGE_CEPHPOOL      = '50015'
ERR_HOST_CONNECTION     = '50016'
ERR_VM_MISSING          = '50017'


ERROR_CN = {
    ERR_AUTH_NO_LOGIN       : '用户未登录',
    ERR_AUTH_LOGIN          : '登录失败',
    ERR_AUTH_LOGOUT         : '注销失败',
    ERR_AUTH_PERM           : '权限错误',
    ERR_GROUP_ID            : '集群ID错误',
    ERR_HOST_ID             : '宿主机ID错误',
    ERR_IMAGE_ID            : '镜像ID错误',
    ERR_CEPH_ID             : 'CEPH资源池ID错误',
    ERR_VLAN_ID             : '网段ID错误',
    ERR_VM_UUID             : '虚拟机UUID错误',
    ERR_VM_NO_OP            : '虚拟机操作类型错误',
    ERR_ARGS_VM_VCPU        : '虚拟机参数错误：VCPU',
    ERR_ARGS_VM_MEM         : '虚拟机参数错误：内存',
    ERR_ARGS_VM_EDIT_NONE   : '虚拟机参数错误：没有修改任何参数',
    ERR_ARGS_REQUIRED       : '虚拟机参数错误：缺少参数',
    ERR_ARGS_VM_CREATE_NO_VLANTYPE : '虚拟机参数错误：创建虚拟机时未指定网络类型',
    ERR_DISK_NAME           : '磁盘UUID错误',
    ERR_CENTER_ID           : '分中心ID错误',
    ERR_VM_NAME             : '虚拟机名称错误',
    ERR_VLAN_TYPE_ID        : '网络类型ID错误',
    ERR_VLAN_FILTER_NONE    : '无可用网段',
    ERR_HOST_FILTER_NONE    : '无满足要求的宿主机',
    ERR_VM_MIGRATE_DIFF_CEPH: '不能跨ceph集群迁移',
    ERR_VM_MIGRATE_LIVING   : '运行状态不能迁移',
    ERR_HOST_CLAIM          : '宿主机自愿申请失败',
    ERR_VM_RESET_LIVING     : '运行状态不能重置',
    ERR_VM_EDIT_LIVING      : '运行状态不能修改',
    
    ERR_ARGS_DECORATOR      : '装饰器使用有误',
    ERR_PROCESS             : '处理失败',
    ERR_LOG                 : '日志记录失败',
    ERR_VLAN_NO_FIND        : '没有找到任何网段',
    ERR_VM_DEFINE           : '虚拟机创建失败',
    ERR_VM_OP               : '操作失败',
    ERR_VM_EDIT_REMARKS     : '虚拟机备注修改失败',
    ERR_VM_EDIT             : '虚拟机修改失败',
    ERR_VM_MIGRATE          : '虚拟机迁移失败',
    ERR_DISK_INIT           : '虚拟机磁盘初始化失败',
    ERR_DISK_ARCHIVE        : '虚拟机归档失败',
    ERR_IMAGE_INFO          : '获取镜像信息失败' ,
    ERR_IMAGE_CEPHHOST      : '获取镜像所属CEPH集群失败',
    ERR_IMAGE_CEPHPOOL      : '获取镜像所属CEPH资源池失败',
    ERR_HOST_CONNECTION     : '宿主机连接失败',
    ERR_VM_MISSING          : '虚拟机连接失败'      

}

STRERR_EN = {
    ERR_ARGS_DECORATOR:     'decorator args_required can not used here.',
    ERR_ARGS_REQUIRED:    'args not exists.',
    ERR_PROCESS:            'processing error.',
    ERR_LOG:                'log error.',
    ERR_AUTH_NO_LOGIN:      'user not login.',
    ERR_AUTH_LOGIN:         'login error.',
    ERR_AUTH_LOGOUT:        'logout error.',
    ERR_AUTH_PERM:          'permission error.',
    ERR_GROUP_ID:           'group id error.',
    ERR_HOST_ID:            'host id error.',
    ERR_IMAGE_ID:           'image id error.',
    ERR_CEPH_ID:            'ceph id error.',
    ERR_VLAN_NO_FIND:       'vlan not find.',
    ERR_VLAN_ID:            'vlan id error.',
    ERR_VM_UUID:            'vm uuid error.',
    ERR_VM_DEFINE:          'vm define error.',
    ERR_VM_OP:              'vm opperation error.',
    ERR_VM_NO_OP:           'op name error.',
    ERR_ARGS_VM_VCPU:       'vm args vcpu error.',
    ERR_ARGS_VM_MEM:        'vm args memory error.',
    ERR_ARGS_VM_EDIT_NONE:  'no args error.',
    ERR_VM_EDIT_REMARKS:    'edit remarks of vm error.',
    ERR_VM_EDIT:            'edit vm error.',
    ERR_VM_MIGRATE:         'migrate error.',
    ERR_ARGS_VM_CREATE_NO_VLANTYPE: 'net_type_id or vlan_id required.',
    ERR_DISK_INIT:          'init disk error.',
    ERR_DISK_ARCHIVE:       'archive disk error.',
    ERR_DISK_NAME:          'disk name error.',
    ERR_IMAGE_INFO:         'get image info error.',
    ERR_IMAGE_CEPHHOST:     'get ceph host error.',
    ERR_IMAGE_CEPHPOOL:     'get ceph pool error.'
}

class Error(Exception):
    err = ''
    def __init__(self, err):
        self.err = err
    