## v3.1.11
* 虚拟机vms模型增加 vm_status、last_ip 字段， vm_status（正常、搁置）
* 增加虚拟机搁置、恢复、删除、查询列表、删除接口
* 调整vlan子网模型字段：网桥名，vlan_id，vlan描述
* 增加搁置、恢复界面
* api 相关接口增加虚拟机状态判断
* 云硬盘后端存储池增加enable可用字段，响应内容增加dev设备名称
* 硬盘储存池配额列表增加enable参数过滤可用的存储池


## v3.1.10   
* v p n api路由无法匹配包含字符“.”的账户名的问题修复  提交人：shun
* 增加镜像虚拟机功能（更新后需添加127.0.0.1宿主机、添加镜像专用网络） 提交人：shun
* 修改部分Model提示词； 提交人：shun
* 统计报表界面优化； 提交人：shun
* 增加后台管理导航页面； 提交人：shun
* 镜像增加标准化的字段； 提交人：shun
* 云主机删除时卸载硬盘失败的bug修复，vm元数据对象删除后会设置主键uuid为None，而后无法正常获取到uuid;  提交人：shun
* vm模型增加镜像相关字段，记录vm创建时的系统镜像信息，供后续vm的相关操作使用；因为image信息可能随时修改，所以不再通过外键使用最新的image信息;  提交人：shun
* 分中心修改成数据中心； 提交人：wanghuang
* 增加全局配置表页面title、novnchttp使用协议； 提交人：wanghuang
* 增加增加云主机初始化用户信息； 提交人：wanghuang
* 日志格式修改;  提交人：wanghuang


## v3.1.9
* 后台宿主机列表增加action，测试宿主机是否可连接和更新宿主机资源使用量   
* 增加VPNActive、VPNDeactive 激活停用vpn接口和测试用例  
* "关于"网页修改，增加当前版本时间和变更日志链接  

## v3.1.8
* 更新内存计量单位为GB（接口、功能操作）；
* 建立宿主机与物理服务器OneToOne关联；
* 升级PyJWT、djangorestframework库版本；

## v3.1.7
* 基于CentOS9, 升级到Python3.9，及依赖包升级  
* 添加spice和novnc的html5客户端静态文件到static/console目录下  

## v3.1.6
* 用户注册功能是否启用可以配置的实现  
* ListVlan api当用户没有任何宿主机组访问权限时返回所有vlan的问题修复  
* AppVPN api创建的vpn账户默认未激活  
* 移除model ImageType,ListImages响应数据增加镜像大小size，资源配额视图饼形图改为已用和可用  
* add DetailImage api and testcase  
* django, uwsgi版本升级  

## v3.1.5
* vm动态迁移优化  
* vm换镜像时disk_type改为RBD,当vm domain name不是hex uuid时获取vnc找不到domain的问题  
* 当vm系统盘是宿主机本地盘时, vm列表一些vm操作选项不可用  
* VmInstance、VmDomain相关代码优化  
* vm创建api增加sys_disk_size,可指定系统盘容量大小  
* vms manager部分代码拆分抽象封装类VmInstance、VmBuilder、VmXMLBuilder  
* vm系统盘扩容api和view  
* vm add sys_disk_size  
* image model add size  
* 因chartjs更新，统计报表图形修复  
* 支持spice远程控制台  
* ServerDetail api response add 'host_info' data  

## v3.1.4
* 可用资源配额 
* 硬盘支持vm运行状态下挂载 
* vm动态迁移优化

## v3.1.3
* vm动态迁移 
* vm内存、io信息图标实现查询显示 
* 其他一些改进优化

## v3.1.2
* upgrade django3.2 
* vdisk和vm在同一个分中心可挂载

## v3.1.1
* 新增about view；
* API异常响应内容增加错误码，自定义异常处理；
* drf-simplejwt不兼容PyJWT2.0的bug；
* network mac ip生成函数和配置文件导出函数优化修改；
* CreateVdisk api增加权限检查；

## v3.1.0
* admin系统镜像image列表增加filter by center；   
* vm强制删除修改，宿主机不可连接时强制删除，vm归档记录增加host_released字段，标记宿主机上资源是否清理释放；
* admin vm归档记列表增加2个action操作，释放宿主机上资源和删除vm系统镜像ceph rbd；
* list macip的分页器默认每页256；
* host未激活时不显示在vm列表视图host过滤条件中的问题修复；
* libvirt ssh连接宿主机认证失败时禁止询问密码;
* vm miss fix api，宿主机上vm丢失时尝试修复;
* vm强制迁移，源宿主机不可连接时，继续迁移到目标主机；
* vlan与center、host直接从属关系解除，改为属于group，删除vlan type model；
* ListVlan api增加query参数group_id和available；

## v3.0.0 
* vm创建、删除、开机、关机等基础功能;
* vm配置修改、重置系统镜像、迁移、快照、回滚等;
* 硬盘，创建、删除、挂载、卸载等;

## v3.0.1
* PCI设备挂载、卸载功能;
* vm迁移、重置镜像有关pci设备修改, vm详细信息API增加挂载的硬盘和PCI设备信息;
* API返回ISO格式时间数据;
* 可挂载硬盘的vm查询、vm可挂载的硬盘查询API;

## v3.0.2
* vm相关一些代码整理优化
* html模板一些修改
* 重置vm系统（恢复系统盘至创建时状态）
* 系统镜像快照protected

## v3.0.3
* 增加pcservers app，
* 创建虚拟机可以只指定分中心
* flavor硬件配置样式(代替vcpu和mem参数)，flavor api
* 虚拟机修改密码api
* 子网vlan属于分中心center

## v3.0.4
* 创建vm时指定flavor或自定义直接指定cpu和mem配置   
* pci挂载卸载bug修复   
* add vpn app   
* 创建vm api通过参数指定分配公网或私网ip   

## v3.0.5
* 增加vpn配置文件和ca证书下载api   
* 分页相关html模板修改  

## v3.0.6
* 修复host未激活时不显示在vm列表页host过滤条件中的问题
* vm归档记录增加host_released字段，标记宿主机上的vm资源是否释放；
  在宿主机无法访问，强制删除vm时，会标记宿主机上的vm资源未释放；
* admin后台vm归档记录表增加2个action操作，清除vm的系统盘和释放vm在宿主机上的资源；
* macip分页器修改，每页默认256条数据
* admin后台image增加分中心center过滤
