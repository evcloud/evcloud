### v4.2.0

vpn 部分增加 vpn服务IP字段
更新命令是在代码目录下（/home/uwsgi/evcloud/）
1. 停止服务
   ````
   systemctl stop evcloud.service
   systemctl stop evcloud_vnc.service
   systemctl stop evcloud_openvpn.service # 配置文件有修改
2. 备份数据库

3. 更新代码
   ````
   git status # 查看 是否有手动修改的内容，并记录
   git checkout . # 丢弃修改的内容
   git pull origin master
   git fetch --tag
4. 执行数据库操作
   ````
   python manage.py migrate --plan # 查看是否有数据表修改
   python manage.py migrate
5. 收集静态文件
   ````
   python manage.py collectstatic
6. 配置 openvpn 服务文件
   ``````
   00_script/openvpn_service.conf
   需要将 认证信息填入，同时确认 auth-user-pass-verify、push、client-connect、client-disconnect信息
   执行 config_systemctl.sh (如果没有evcloud_openvpn.service 服务)
6. 启动服务
   ``````
   systemctl start evcloud.service
   systemctl start evcloud_vnc.service
   systemctl start evcloud_openvpn.service

### v4.1.2

主要修改配置文件

1. 停止服务
2. 更新代码
3. 重新执行 00_script 中 config_systemctl.sh 文件
4. openvpn 认证文件要复制到 00_script/openvpn_crt目录下
5. openvpn 启动配置文件到 00_script 下找
6. 启动服务

### v4.0.0 v4.0.1 v4.0.2 v4.0.3 v4.0.4 v4.1.0

### v4.1.1

更新命令是在代码目录下（/home/uwsgi/evcloud/）

1. 停止服务

```shell
  v4.0.5 之前版本更新
  systemctl stop evcloud.service
  systemctl stop evcloud-vnc.service 
  执行 00_shell/config_systemctl.sh  
   evcloud-vnc.service  更名为 evcloud_vnc.service
   如果软连接无法生效 删除软连接 执行如下命令
   cp /home/uwsgi/evcloud/evcloud.service /usr/lib/systemd/system/ -f
   cp /home/uwsgi/evcloud/evcloud_vnc.service /usr/lib/systemd/system/ -f
   v4.0.5 之后版本更新
   
    systemctl stop evcloud.service
    systemctl stop evcloud_vnc.service 
   
```

2. 备份数据库

```shell
mysqldump -u root -p  数据库名称 > 文件
```

3. 拉取gitee代码

```shell

git branch   # 查看更新哪个分支  标记* 的是当前使用的分支 一般会更新带 * 的分支
git pull origin 分支名称
git fetch --tags  # 拉取版本信息
```

4. 更新依赖包

```shell
pip install -r requirements.txt
```

5. 迁移文件 (未有数据库字段的改动，不需要执行)

```shell
python manage.py migrate --plan  # 检测是否有迁移文件， 
  # 如果出现如下内容，则不需要 执行 python manage.py migrate 命令
    Planned operations:
    No planned migration operations.
    
python manage.py migrate  # 有迁移
```

6. 收集静态文件

```shell
python manage.py collectstatic 
```

7. 启动服务

```shell
  v4.0.5 之前版本更新
  systemctl start evcloud
  systemctl start evcloud-vnc.service 
  
  v4.0.5 之后版本更新
  systemctl start evcloud
  systemctl start evcloud_vnc.service 
```

### v3.1.13 v3.1.12b3 v3.1.12b2 v3.1.12b1 v3.1.11

1. 停止服务

```shell
  systemctl stop evcloud.service
  systemctl stop evcloud-vnc.service 
```

2. 备份数据库

```shell
mysqldump -u root -p  数据库名称 > 文件
```

3. 拉取gitee代码

```shell
git pull origin develop
git fetch --tags  # 拉取版本信息
```

4. 迁移文件

```shell
python manage.py migrate --plan  
python manage.py migrate  # 有迁移
```

5. 收集静态文件

```shell
python manage.py collectstatic 
```

6. 启动服务

```shell
  systemctl start evcloud
  systemctl start evcloud-vnc.service 
```