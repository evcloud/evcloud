#!/usr/bin/env python36
# -*- coding: utf-8 -*-

import os
import sys
import time

import MySQLdb  # pip3 install mysqlclient 或者 dnf install python3-mysql.x86_64

# from config import db_Ip, db_User, db_Password, db_DefaultDB, db_Port, db_Table
sys.path.append('/home/uwsgi/evcloud/django_site')
import security as settings
db_Ip = settings.DATABASES['default']['HOST']
db_Port = int(settings.DATABASES['default']['PORT'])
db_User = settings.DATABASES['default']['USER']
db_Password = settings.DATABASES['default']['PASSWORD']
db_DefaultDB = settings.DATABASES['default']['NAME']
db_Table = 'novnc_token'

# mariadb setting
#db_Ip        = '127.0.0.1';
#db_Port      = 3306; 
#db_User      = 'root';
#db_Password  = ''; 
#db_DefaultDB = 'evcloud'


class TokenMysql(object):
    def __init__(self, src):
        self._server = src

    @staticmethod
    def lookup(token):
        try:
            # mysql_conn = MySQLdb.connect(db_Ip, db_User, db_Password, db_DefaultDB, db_Port, charset='utf8')
            mysql_conn = MySQLdb.connect(host=db_Ip, port=db_Port, user=db_User, password=db_Password,
                                         database=db_DefaultDB, charset='utf8mb4')
            # mysql_conn = mysql.connector.connect(**config) # tidb
        except:
            print(f'connect to the server faild!server:{db_Ip}')
            return None
 
        sql_string = f"SELECT ip,port FROM {db_Table} WHERE token = '{token}';"
        mysql_cur = mysql_conn.cursor()    # mysql cursor
        try:
            mysql_cur.execute(sql_string)
        except:
            print('mysql select failed!')
            return None

        result = mysql_cur.fetchone()
        if result is None:
            return None  # token未找到

        ip, port = result
        mysql_cur.close()
        mysql_conn.close()
        return [ip, port]


# 主程序 run by itself
if __name__ == '__main__':
    print("Welcome to use this progress ,by hai! hai@cnic.cn")
    print(time.strftime('服务器当前时间： %Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    programPath = os.path.realpath(__file__)
    print(f"The full path of this program is : {programPath}")
    folderPath = os.path.split(programPath)[0] + '/'
    print(f"The folder path of this program is : {folderPath}")
    print('\n############################    Program Start!#######################\n')

    testClass = TokenMysql('')
    print(testClass.lookup("test"))
    print(testClass.lookup("e82bdeba-b613-4121-b4ae-840564f498ae"))
