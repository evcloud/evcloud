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
