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
ERR_VOLUME_QUOTA_G      = '40038'
ERR_VOLUME_QUOTA_V      = '40039'
ERR_VM_CREATE_ARGS_HOST = '40040'
ERR_VM_CREATE_ARGS_VLAN = '40041'
ERR_VM_VCPU             = '40042'
ERR_VM_MEM              = '40043'
ERR_DISKSNAP_ID         = '40044'
ERR_VM_CREATE_SNAP_LIVING     = '40045'
ERR_VM_MIGRATE_SAME_HOST= '40046'


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
ERR_GPU_EDIT_REMARKS    = '50018'
ERR_GPU_MOUNT           = '50019'
ERR_GPU_UMOUNT          = '50020'
ERR_CEPH_MV             = '50021'
ERR_CEPH_RM             = '50022'
ERR_CEPH_CLONE          = '50023'
ERR_CEPH_CREATE         = '50024'
ERR_CEPH_RESIZE         = '50025'
ERR_CEPH_SNAP           = '50026'
ERR_CEPH_PROTECT        = '50027'
ERR_VOLUME_CREATE_DB    = '50028'
ERR_VOLUME_CREATE_NOPOOL= '50029'
ERR_VOLUME_DELETE_DB    = '50030'
ERR_VOLUME_MOUNT        = '50031'
ERR_VOLUME_UMOUNT       = '50032'
ERR_VOLUME_RESIZE       = '50033'
ERR_VOLUME_REMARKS      = '50034'
ERR_VM_HOST_FILTER      = '50033'
ERR_VM_CREATE_DB        = '50034'
ERR_VM_CREATE_DISK      = '50035'
ERR_VM_DEL_GPU_MOUNTED  = '50036'
ERR_VM_DEL_VOL_MOUNTED  = '50037'
ERR_MOUNT_RUNNING       = '50038'
ERR_UMOUNT_RUNNING      = '50039'
ERR_VLAN_EDIT_REMARKS   = '50040'
ERR_VM_RESET            = '50041'
ERR_VM_CREATE_SNAP      = '50042'
ERR_VM_ROLLBACK_SNAP    = '50043'
ERR_VM_EDIT_REMARKS     = '50044'

ERR_USERNAME            = '60001'
ERR_USER_DB             = '60002'
ERR_INT_VOLUME_SIZE     = '60003'
ERR_VOLUME_ID           = '60004'
ERR_PERM_DEL_VOLUME     = '60005'
ERR_CEPHPOOL_ID         = '60006'
ERR_VM_ID               = '60007'
ERR_HOST_IPV4           = '60008'
ERR_GPU_ID              = '60009'
ERR_GPU_ADDRESS         = '60010'
ERR_DEL_MOUNTED_VOLUME  = '60011'

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
    ERR_VLAN_FILTER_NONE    : '无可用网段或IP地址用尽',
    ERR_HOST_FILTER_NONE    : '无满足要求的宿主机',
    ERR_VM_MIGRATE_DIFF_CEPH: '不能跨ceph集群迁移',
    ERR_VM_MIGRATE_LIVING   : '运行状态不能迁移',
    ERR_HOST_CLAIM          : '宿主机自愿申请失败',
    ERR_VM_RESET_LIVING     : '运行状态不能重置',
    ERR_VM_EDIT_LIVING      : '运行状态不能修改',
    ERR_VOLUME_QUOTA_G      : '集群容量超配额',
    ERR_VOLUME_QUOTA_V      : '云硬盘容量超配额',
    ERR_VM_CREATE_ARGS_HOST : '云主机创建参数错误，必须指定宿主机或集群',
    ERR_VM_CREATE_ARGS_VLAN : '云主机创建参数错误，必须指定网段或网络类型',
    ERR_VM_VCPU             : '云主机参数错误，VCPU必须为正整数',
    ERR_VM_MEM              : '云主机参数错误，MEM必须为正整数',
    ERR_DISKSNAP_ID         : '虚拟机快照ID错误',
    ERR_VM_CREATE_SNAP_LIVING : '运行状态不能执行快照回滚',
    ERR_VM_MIGRATE_SAME_HOST  : '迁移的目标宿主机不能是原宿主机',

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
    ERR_VM_MISSING          : '虚拟机连接失败',
    ERR_GPU_EDIT_REMARKS    : 'GPU备注修改失败',
    ERR_GPU_MOUNT           : 'GPU挂载失败',
    ERR_GPU_UMOUNT          : 'GPU卸载失败',
    ERR_CEPH_MV             : 'ceph mv操作失败',
    ERR_CEPH_RM             : 'ceph rm操作失败',
    ERR_CEPH_CLONE          : 'ceph clone操作失败',
    ERR_CEPH_CREATE         : 'ceph create操作失败',
    ERR_CEPH_RESIZE         : 'ceph resize操作失败',
    ERR_CEPH_SNAP           : 'ceph 创建快照失败',
    ERR_CEPH_PROTECT        : 'ceph 保护快照失败',
    ERR_VOLUME_CREATE_DB    : '云硬盘创建失败，写入数据库失败',
    ERR_VOLUME_CREATE_NOPOOL: '云硬盘创建失败，无资源池',
    ERR_VOLUME_DELETE_DB    : '云硬盘删除失败',
    ERR_VOLUME_MOUNT        : '云硬盘挂载失败',
    ERR_VOLUME_UMOUNT       : '云硬盘卸载失败', 
    ERR_VOLUME_RESIZE       : '云硬盘修改容量失败',
    ERR_VOLUME_REMARKS      : '云硬盘写入备注失败',
    ERR_VM_HOST_FILTER      : '宿主机筛选失败',
    ERR_VM_CREATE_DB        : '云主机创建失败，数据库写入失败',
    ERR_VM_CREATE_DISK      : '云主机创建失败，初始化磁盘失败',
    ERR_VM_DEL_GPU_MOUNTED  : '云主机删除失败，有GPU设备未卸载',
    ERR_VM_DEL_VOL_MOUNTED  : '云主机删除失败，有云硬盘未卸载',
    ERR_MOUNT_RUNNING       : '运行中的云主机不能进行挂载操作',
    ERR_UMOUNT_RUNNING      : '运行中的云主机不能进行卸载操作',
    ERR_VLAN_EDIT_REMARKS   : '网段备注修改失败', 
    ERR_VM_RESET            : '虚拟机重置镜像失败', 
    ERR_VM_CREATE_SNAP      : '虚拟机快照创建失败',
    ERR_VM_ROLLBACK_SNAP    : '虚拟机快照回滚失败',
    ERR_VM_EDIT_REMARKS     : '虚拟机快照备注修改失败',    

    ERR_USERNAME            : '有户名有误',
    ERR_USER_DB             : 'DBUser对象有误',
    ERR_INT_VOLUME_SIZE     : '磁盘容量参数必须为正整数',
    ERR_VOLUME_ID           : 'CEPH块ID有误',
    ERR_PERM_DEL_VOLUME     : '权限错误：无权删除VOLUME',
    ERR_CEPHPOOL_ID         : 'CEPH资源池ID错误',
    ERR_VM_ID               : 'VM UUID有误',
    ERR_HOST_IPV4           : '宿主机IP地址有误',
    ERR_GPU_ID              : 'GPU ID有误',
    ERR_GPU_ADDRESS         : 'GPU 标识有误',
    ERR_DEL_MOUNTED_VOLUME  : '不能删除已挂载VOLUME',
}


class Error(Exception):
    err = ''
    def __init__(self, err):
        self.err = err
    #     if err in ERROR_CN:
    #         print(err, ERROR_CN[err])
    # 