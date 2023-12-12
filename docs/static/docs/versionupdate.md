### v4.0.0 v4.0.1 v4.0.2
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

4. 更新依赖包
```shell
pip install -r requirements.txt
```

5. 迁移文件 (未有数据库字段的改动，不需要执行)
```shell
python manage.py migrate --plan  
python manage.py migrate  # 有迁移
```

6. 收集静态文件
```shell
python manage.py collectstatic 
```

7. 启动服务 
```shell
  systemctl start evcloud
  systemctl start evcloud-vnc.service 
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