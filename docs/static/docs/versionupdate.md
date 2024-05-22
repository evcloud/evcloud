### v4.6.0

注意：用户操作日志增加IP字段，需要迁移操作，及时做好备份操作。
1. 所有节点停止服务
   ```
   systemctl stop evcloud.service
   systemctl stop evcloud_vnc.service
   ``` 
2. 备份数据库
   ```shell
   mysqldump -u user -p  数据库名称 > 文件
   tidb：
   mysqldump -u user -h ip -P 4000 -p  数据库名称 > 文件
   ```

3. 更新代码前查看是否有手动修改的文件，妥善处理
   ```
   git status # 查看 是否有手动修改的内容，并记录 
   
   git checkout file  # 代码更新后，手动恢复修改的文件内容

   ```
4. 更新代码
   ```
   git pull origin master
   git fetch --tag
   python manage.py migrate --plan # 查看是否有数据表修改  如果有多个节点使用同一个数据库，只在其中一个节点执行数据迁移操作就行
   ····
   # 如果出现如下内容，则不需要 执行 python manage.py migrate 命令
    Planned operations:
    No planned migration operations.
   ····
   python manage.py migrate  # 数据迁移
   pip install -r 00_script/depend/requirements.txt
   python manage.py collectstatic
   python manage.py check_global_config  # 检测和添加默认站点参数，如果没有安装其他版本
   
   其他节点执行：
    rsync -avP --delete ip:/home/uwsgi/evcloud/  /home/uwsgi/evcloud/
    并到每个节点服务中执行pip install -r /home/uwsgi/evcloud/00_script/depend/requirements.txt 下载依赖包
   ```

5. 启动服务
   ``````
   systemctl start evcloud.service
   systemctl start evcloud_vnc.service
   

### v4.5.0
注意：vpn 配置文件字段删除，改成站点参数配置。更新之前需要记录原有的vpn配置信息。
1. 停止服务
   ```
   systemctl stop evcloud.service
   systemctl stop evcloud_vnc.service
   ``` 
2. 备份数据库
   ```shell
   mysqldump -u user -p  数据库名称 > 文件
   tidb：
   mysqldump -u user -h ip -P 4000 -p  数据库名称 > 文件
   ```

3. 更新代码前查看是否有手动修改的文件，妥善处理
   ```
   git status # 查看 是否有手动修改的内容，并记录 
   
   git checkout file  # 代码更新后，手动恢复修改的文件内容

   ```
4. 更新代码
   ```
   git pull origin master
   git fetch --tag
   python manage.py migrate --plan # 查看是否有数据表修改  如果有多个节点使用同一个数据库，只在其中一个节点执行数据迁移操作就行
   ····
   # 如果出现如下内容，则不需要 执行 python manage.py migrate 命令
    Planned operations:
    No planned migration operations.
   ····
   python manage.py migrate  # 数据迁移
   pip install -r 00_script/depend/requirements.txt
   python manage.py collectstatic
   python manage.py check_global_config  # 检测和添加默认站点参数
   
   其他节点执行：
    rsync -avP --delete ip:/home/uwsgi/evcloud/  /home/uwsgi/evcloud/
    并到每个节点服务中执行pip install -r /home/uwsgi/evcloud/00_script/depend/requirements.txt 下载依赖包
   ```

5. 启动服务
   ``````
   systemctl start evcloud.service
   systemctl start evcloud_vnc.service
   


### v4.4.1
1. 停止服务
   ```
   systemctl stop evcloud.service
   systemctl stop evcloud_vnc.service
   ``` 
2. 备份数据库
   ```shell
   mysqldump -u user -p  数据库名称 > 文件
   tidb：
   mysqldump -u user -h ip -P 4000 -p  数据库名称 > 文件
   ```

3. 更新代码前查看是否有手动修改的文件，妥善处理
   ```
   git status # 查看 是否有手动修改的内容，并记录 
   
   git checkout file  # 代码更新后，手动恢复修改的文件内容

   ```
4. 更新代码
   ```
   git pull origin master
   git fetch --tag
   python manage.py migrate --plan # 查看是否有数据表修改  如果有多个节点使用同一个数据库，只在其中一个节点执行数据迁移操作就行
   ····
   # 如果出现如下内容，则不需要 执行 python manage.py migrate 命令
    Planned operations:
    No planned migration operations.
   ····
   python manage.py migrate  # 数据迁移
   pip install -r 00_script/depend/requirements.txt
   python manage.py collectstatic
   
   其他节点执行：
    rsync -avP --delete ip:/home/uwsgi/evcloud/  /home/uwsgi/evcloud/
    并到每个节点服务中执行pip install -r /home/uwsgi/evcloud/00_script/depend/requirements.txt 下载依赖包
   ```

5. 启动服务
   ``````
   systemctl start evcloud.service
   systemctl start evcloud_vnc.service



### v4.4.0
1. 停止服务
   ```
   systemctl stop evcloud.service
   systemctl stop evcloud_vnc.service
   ``` 
2. 备份数据库
   ```shell
   mysqldump -u user -p  数据库名称 > 文件
   tidb：
   mysqldump -u user -h ip -P 4000 -p  数据库名称 > 文件
   ```

3. 更新代码前查看是否有手动修改的文件，妥善处理
   ```
   git status # 查看 是否有手动修改的内容，并记录 
   
   git checkout file  # 代码更新后，手动恢复修改的文件内容

   ```
4. 更新代码
   ```
   git pull origin master
   git fetch --tag
   python manage.py migrate --plan # 查看是否有数据表修改  如果有多个节点使用同一个数据库，只在其中一个节点执行数据迁移操作就行
   ····
   # 如果出现如下内容，则不需要 执行 python manage.py migrate 命令
    Planned operations:
    No planned migration operations.
   ····
   python manage.py migrate  # 数据迁移
   pip install -r 00_script/depend/requirements.txt
   python manage.py collectstatic
   
   其他节点执行：
    rsync -avP --delete ip:/home/uwsgi/evcloud/  /home/uwsgi/evcloud/
    并到每个节点服务中执行pip install -r /home/uwsgi/evcloud/00_script/depend/requirements.txt 下载依赖包
   ```

5. 启动服务
   ``````
   systemctl start evcloud.service
   systemctl start evcloud_vnc.service


### v4.3.0
1. 停止服务
   ```
   systemctl stop evcloud.service
   systemctl stop evcloud_vnc.service
   ``` 
2. 备份数据库
   ```shell
   mysqldump -u user -p  数据库名称 > 文件
   ```

3. 更新代码前查看是否有手动修改的文件，妥善处理
   ```
   git status # 查看 是否有手动修改的内容，并记录  
   ·········
   如果文件 openvpn_disconnect.py、openvpn_connect.py、openvpn_auth.py 标红, 使用 git checkout 命令如下：
   git checkout 00_script/openvpn_auth.py
   git checkout 00_script/openvpn_connect.py
   git checkout 00_script/openvpn_disconnect.py
      
   注意： 这三个文件在上一个版本没有设置权限，需要手动修改权限导致标红，代码中已经设置文件权限，所已需要提前操作。
         openvpn_server.conf 这个文件标红，不用处理。
         其他标红文件妥善处理
   ·········
   ```
4. 更新代码
   ```
   git pull origin master
   git fetch --tag
   python manage.py migrate --plan # 查看是否有数据表修改  如果有多个节点使用同一个数据库，只在其中一个节点执行数据迁移操作就行
   ····
   # 如果出现如下内容，则不需要 执行 python manage.py migrate 命令
    Planned operations:
    No planned migration operations.
   ····
   python manage.py migrate  # 数据迁移
   pip install -r 00_script/depend/requirements.txt
   python manage.py collectstatic
   
   ```

5. 启动服务
   ``````
   systemctl start evcloud.service
   systemctl start evcloud_vnc.service
   systemctl restart evcloud_openvpn.service


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
   pip install -r requirements.txt
   
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

### v4.1.0
### v4.0.4 
### v4.0.3 
### v4.0.2 
### v4.0.1 
### v4.0.0
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

### v3.1.11
### v3.1.12b1 
### v3.1.12b2 
### v3.1.12b3 
### v3.1.13 

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