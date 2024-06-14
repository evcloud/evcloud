## v4.7.0
2024-06-14
* xml模板数据表增加cpu识别参数字段max_cpu_socket，创建时插入xml信息  提交人：wanghuang
* 虚拟机错误信息表增加“解决”字段  提交人：wanghuang
* 访问IP白名单更名 IP访问白名单  提交人：wanghuang


## v4.6.0
2024-05-22
* 用户操作日志增加IP信息  提交人：wanghuang
* 用户操作日志页面内容调整到资源统计管理页面中  提交人：wanghuang
* 强制删除虚拟机，只记录不返回错误信息，由管理人员负责清除数据  提交人：wanghuang
* 镜像发布功能优化：删除制作镜像过程中的快照  提交人：wanghuang
* 站点默认参数删除ca证书信息  提交人：wanghuang
* 增加中英文翻译内容  提交人：wanghuang


## v4.5.0
2024-05-15
* 修复挂载接口因记录日志报错  提交人：wanghuang
* 删除 vpn 原有的配置字段，改成站点参数配置  提交人：wanghuang
* vpn 配置文件和ca证书名称和内容在站点参数中设置  提交人：wanghuang
* 下载vpn配置文件不做记录  提交人：wanghuang
* 管理员IP白名单修改为访问IP白名单  提交人：wanghuang
* 查询版本号接口返回格式修改:v4.5.0  提交人：wanghuang
* 增加站点参数检测命令：check_global_config  提交人：wanghuang
* 用户登录界面IP 限制，不显示登录框  提交人：wanghuang
* 取消csrf验证  提交人：wanghuang


## v4.4.1
2024-05-11
* 用户界面操作日志视图:删除半年信息日志时间错误修改  提交人：wanghuang
* 从获取url用户信息功能修改  提交人：wanghuang
* 用户日志：vnc 信息添加IP内容，vpn 文件下载增加用户  提交人：wanghuang
* 版本接口不做限制  提交人：wanghuang


## v4.4.0
2024-05-08
* 增加管理员IP白名单  提交人：wanghuang
* api 接口、登录界面增加 IP 限制  提交人：wanghuang
* 用户操作接口获取用户信息方法修改  提交人：wanghuang
* 全局配置内容调整：站点参数、管理员IP白名单、CEPH存储集群、CEPH数据存储池  提交人：wanghuang
* 全局配置字段修改 TextField  提交人：wanghuang
* 站点参数增加 vncUserConfig配置  提交人：wanghuang
* vpn 配置文件接口增加获取vncUserConfig配置文件  提交人：wanghuang
* data 目录权限调整：私钥文件权限 600、ceph 配置文件 644、 data 目录权限 755  提交人：wanghuang


## v4.3.0
2024-04-28
* 数据大屏展示数据汇总接口增加vpn在线数  提交人：wanghuang
* 增加用户操作日志界面及日志清楚按钮  提交人：wanghuang
* 资源配额图表页面合并到资源统计管理页面中  提交人：wanghuang
* 用户操作日志优化：接口查询参数、model字段、url信息提取、界面 提交人：wanghuang
* 检测优化：一键检测和批量保存限制页面显示内容，去掉通过输入IP信息检测功能  提交人：wanghuang
* 站点配置默认信息会自动创建  提交人：wanghuang
* 后端app根据自定义规则排序  提交人：wanghuang
* 导航栏高亮部分不显示调整  提交人：wanghuang
* 后台管理导航页面修改部分信息：全局配置信息、vpn 日志等  提交人：wanghuang
* vpn页面增加"删除非激活用户按钮","清理半年前日志"按钮  提交人：wanghuang
* vpn 后端显示"VNP服务IP"字段  提交人：wanghuang
* openvpn部分文件 权限调整  提交人：wanghuang
* 依赖包更新  提交人：wanghuang


## v4.2.0
2024-04-17
* 增加数据大屏展示数据汇总接口   提交人：wanghuang
* 增加 openvpn service 服务文件，config_systemctl 增加 openvpn service 服务开机启动操作   提交人：wanghuang
* openvpn auth 内容配置路径修   提交人：wanghuang
* vpn 删除过期日期，标题头部按钮调整，增加 vpn服务IP字段   提交人：wanghuang
* vpn服务认证内容移动到openvpn_server.conf中，删除openvpn_crt目录   提交人：wanghuang
* 资源管理检测大页内存信息格式不对优化，标题信息调整   提交人：wanghuang
* mac_ip 显示字段顺序调整   提交人：wanghuang


## v4.1.2
2024-04-11
* 00_shell 修改为 00_script   提交人：wanghuang
* openvpn 配置文件归并到 00_script   提交人：wanghuang
* 服务启动文件重命名，服务文件启动路径修改   提交人：wanghuang
* openvpn_crt 存放 认证文件   提交人：wanghuang


## v4.1.1
2024-04-10
* 全局配置表修改   提交人：wanghuang
* 增加api log用户日志记录，提供查询接口   提交人：wanghuang
* 后台信息中英文翻译    提交人：wanghuang
* 数据中心增加 ssh 公钥配置  提交人：wanghuang
* 修正openvpn相关执行文件   提交人：wanghuang
* cpeh删除快照 记录ImageNotFound错误   提交人：wanghuang
* 用户注册信息中英文翻译    提交人：李跃鹏
* 优化批量检测功能    提交人：wanghuang

## v4.1.0
2024-02-20
* 修复 vnc 无法使用 sshkey 连接   提交人：wanghuang
* 增加接口错误记录   提交人：wanghuang
* 统计报表更名资源统计管理   提交人：wanghuang
* 资源统计管理增加宿主机cpu、内存信息检测和保存功能   提交人：wanghuang
* 资源统计管理增加宿主机一键检测和批量保存功能   提交人：wanghuang


## v4.0.5
2024-01-05
* 数据中心增加 ssh 配置， 宿主机连接增加 ssh参数  提交人：wanghuang
* 镜像页面调整镜像机状态、备注栏加宽  提交人：wanghuang
* 服务文件添加到 00_shell 文件中， 建立软连接  提交人：wanghuang


## v4.0.4
2024-01-02
* 增加Rocky系统类型选项  提交人：wanghuang
* apidocs 增加权限访问  提交人：wanghuang
* 可用总资源配额和已用配额信息接口增加数据中心参数  提交人：wanghuang
* 配额查询接口增加参数’center_id‘优化  提交人：shun


## v4.0.3
2023-12-18
* 系统镜像基于宿主机创建，可选择宿主机IP  提交人：wanghuang
* 国际化支持  提交人：wanghuang
* 获取可用总资源配额和已用配额信息接口增加公网私网数据统计  提交人：wanghuang
* vpn 删除ca证书  提交人：wanghuang
* vpn 列表 配置文件按钮和创建VPN按钮位置更新  提交人：wanghuang
* 系统资源不统计127.0.0.1 cpu和内存  提交人：wanghuang
* 后端vlan显示镜像专用标签  提交人：wanghuang


## v4.0.2
2023-12-12
* 增加镜像发布功能  提交人：wanghuang  
* 增加镜像错误日志记录  提交人：wanghuang  
* 增加保护快照删除功能  提交人：wanghuang  
* 优化ipv6配置文件导出报错   提交人：wanghuang  
* 修复本地硬盘挂载出现同名错误   提交人：wanghuang  
* 本地资源描述信息更新：增加 address 列表   提交人：wanghuang  


## v4.0.1
2023-11-27
* 云主机全部修改成虚拟机  提交人：wanghuang   
* tidb 4.2.1 迁移文件遇见primary_key无法修改问题  提交人：wanghuang   
* 优化屏蔽vlan功能：不能重复添加数据、创建虚拟机管理员无法选择网络问题  提交人：wanghuang   
* 依赖包更新  提交人：wanghuang   


## v4.0.0
2023-10-07
* django 版本由 3.2.13 升级到 4.2.5 提交人：wanghuang   
* 版本字段更改：ugettext_lazy, ugettext, ungettext
* 增加 vpn 登录信息界面  提交人：wanghuang
* 优化 vlan 信息不存在时， 屏蔽vlan功能错误提示  提交人：wanghuang
* novnc升级到1.4.0 ,spice升级到0.3.0  提交人：wanghuang
* 优化 novnc 数据库连接  提交人：wanghuang


## v3.1.13
2023-09-19
* novnc url 地址连接优化  提交人：wanghuang
* vpn 日志字段信息调整  提交人：wanghuang
* vpn 脚本连接数据库字符集调整  提交人：wanghuang
* vpn 配置脚本调整文件权限  提交人：wanghuang


## v3.1.12b3
2023-09-19
* 增加对用户屏蔽vlan功能  提交人：wanghuang
* 增加 vpn 日志登录登出记录功能  提交人：wanghuang
* 修改云硬盘 cache 模式为 writethrough  提交人：wanghuang
* 使用说明修改和完善：增加功能指南、完善版本更新流程、完善搭建环境说明  提交人：wanghuang
* 优化 vlan 接口，增加 lookup_field配置  提交人：wanghuang
* 优化镜像接口查询参数  提交人：wanghuang
* 修复 pci 获取模板出现的问题  提交人：wanghuang
* 修复 可用总资源配额和已用配额信息接口参数无效问题  提交人：wanghuang
* 修复创建虚拟机内存单位参数无效问题  提交人：wanghuang
* 测试用例：mcaip接口、pci接口、资源统计信息接口、云硬盘数据接口、宿主机组接口、宿主机接口、硬件配置样式接口、系统镜像接口、  提交人：wanghuang


## v3.1.12b2
* 支持ipv6  提交人：wanghuang
* 优化附加IP查询  提交人：wanghuang
* 优化批量生成IP网段限制  提交人：wanghuang


## v3.1.12b1
* 增加虚拟机搁置、恢复服务功能  提交人：wanghuang
* 增加PCIe设备类型：本地硬盘、PCIE硬盘 挂载功能  提交人：wanghuang
* 增加虚拟机附加、移除、搜索IP功能  提交人：wanghuang
* 界面文案修改  提交人：wanghuang
* 优化搁置虚拟机管理员权限  提交人：wanghuang
* 优化附加IP用完后报错 提交人：wanghuang


## v3.1.11
* 虚拟机vms模型增加 vm_status、last_ip 字段， vm_status（正常、搁置） 提交人：wanghuang
* 增加虚拟机搁置、恢复、删除、查询列表、删除接口 提交人：wanghuang
* 调整vlan子网模型字段：网桥名，vlan_id，vlan描述 提交人：wanghuang
* 增加搁置、恢复界面 提交人：wanghuang
* api 相关接口增加虚拟机状态判断 提交人：wanghuang
* 云硬盘后端存储池增加enable可用字段，响应内容增加dev设备名称 提交人：wanghuang
* 硬盘储存池配额列表增加enable参数过滤可用的存储池 提交人：wanghuang


## v3.1.10   
* v p n api路由无法匹配包含字符“.”的账户名的问题修复  提交人：shun
* 增加镜像虚拟机功能（更新后需添加127.0.0.1宿主机、添加镜像专用网络） 提交人：shun
* 修改部分Model提示词； 提交人：shun
* 统计报表界面优化； 提交人：shun
* 增加后台管理导航页面； 提交人：shun
* 镜像增加标准化的字段； 提交人：shun
* 虚拟机删除时卸载硬盘失败的bug修复，vm元数据对象删除后会设置主键uuid为None，而后无法正常获取到uuid;  提交人：shun
* vm模型增加镜像相关字段，记录vm创建时的系统镜像信息，供后续vm的相关操作使用；因为image信息可能随时修改，所以不再通过外键使用最新的image信息;  提交人：shun
* 分中心修改成数据中心； 提交人：wanghuang
* 增加全局配置表页面title、novnchttp使用协议； 提交人：wanghuang
* 增加增加虚拟机初始化用户信息； 提交人：wanghuang
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
