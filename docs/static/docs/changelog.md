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
