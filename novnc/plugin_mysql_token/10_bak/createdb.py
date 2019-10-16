#!/usr/bin/env python36
# -*- coding: utf-8 -*-

import os,sys,time
import MySQLdb    #  pip3 install mysqlclient 或者 dnf install python3-mysql.x86_64

from token_plugin_mysql import db_Ip, db_User, db_Password, db_DefaultDB, db_Port, db_Table
create_db_sql = f"CREATE DATABASE `{db_DefaultDB}` /*!40100 COLLATE 'utf8_general_ci' */"
create_table_sql = f"""CREATE TABLE `{db_Table}` (
	`id` INT(11) NOT NULL AUTO_INCREMENT,
	`token` VARCHAR(300) NOT NULL,
	`ip`    VARCHAR(32)  NOT NULL,
	`port`  VARCHAR(32)  NOT NULL,
	`create_time` DATETIME NULL DEFAULT NULL,
	PRIMARY KEY (`id`)
)
COLLATE='utf8_general_ci'
ENGINE=InnoDB;"""

#主程序 run by itself    
if __name__ == '__main__':
    print("Welcome to use this progress ,by hai! hai@cnic.cn")
    print( time.strftime( '服务器当前时间： %Y-%m-%d %H:%M:%S',time.localtime(time.time()) )  )
    dirPath = os.path.dirname(__file__)
    print(f"This program is under folder : {dirPath}")
    programPath = os.path.realpath(__file__)
    print(f"The full path of this program is : {programPath}")
    folderPath = os.path.split(programPath)[0] + '/'
    print(f"The folder path of this program is : {folderPath}")
    print('\n############################    Program Start!#######################\n')
 
    tmp_DefaultDB = '';
    try:
        mysql_conn =   MySQLdb.connect(db_Ip, db_User, db_Password, tmp_DefaultDB, db_Port, charset='utf8')
    except:
        print('connect to the server faild!server:{0}'.format(db_Ip))
        sys.exit()
    else:
        print('connect success!server:{0}'.format(db_Ip))
 
    #cursor:
    mysql_cur  =   mysql_conn.cursor()
    try:
        print(create_db_sql)
        mysql_cur.execute(create_db_sql)
    except:
        print(f"Can't create DB '{db_DefaultDB}'!server:{db_Ip}")
        print('DB already exists or permission denied')
        print('Try to create table now.')
    else:
        print(f'create DB success!server:{db_Ip}')

    try:
        mysql_cur.execute('use ' + db_DefaultDB + ';')
        print(create_table_sql)
        mysql_cur.execute(create_table_sql)
    except:
        print(f"create table '{db_Table}' faild!server:{db_Ip}")
    else:
        print(f"Create database and table successfully at {db_Ip}" )
    mysql_cur.close()
    mysql_conn.close()
