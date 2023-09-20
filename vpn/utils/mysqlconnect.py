import os
import sys
import time

import MySQLdb  # pip3 install mysqlclient 或者 dnf install python3-mysql.x86_64

sys.path.append('/home/uwsgi/evcloud/django_site')
import security as settings

db_Ip = settings.DATABASES['default']['HOST']
db_Port = int(settings.DATABASES['default']['PORT'])
db_User = settings.DATABASES['default']['USER']
db_Password = settings.DATABASES['default']['PASSWORD']
db_DefaultDB = settings.DATABASES['default']['NAME']
db_Table = 'vpn_vpnlog'


class VNCLogMysql(object):

    def connect(self):
        try:
            mysql_conn = MySQLdb.connect(host=db_Ip, port=db_Port, user=db_User, password=db_Password,
                                         database=db_DefaultDB, charset='utf8mb4')
        except Exception as e:
            raise ValueError(f'连接数据库时错误，服务IP:{db_Ip}, error: {str(e)}')
        return mysql_conn

    def update(self, username, logout_time, bytes_received, bytes_sent):
        mysql_conn = self.connect()
        mysql_cur = mysql_conn.cursor()  # mysql cursor

        result = self.select(mysql_cur=mysql_cur, username=username)

        if result is None:
            raise ValueError(f'数据库中没该用户：{username} 的数据，应该执行此步骤操作。')

        sql = f'UPDATE {db_Table} SET logout_time="{logout_time}", bytes_received={bytes_received}, bytes_sent={bytes_sent} ' \
              f'WHERE id={result[0]}'

        try:
            mysql_cur.execute(sql)
            mysql_conn.commit()
        except Exception as e:
            raise ValueError(f'mysql update failed! {sql}, error: {str(e)}')

        self.close(mysql_cur=mysql_cur, mysql_conn=mysql_conn)

    def insert(self, value):

        mysql_conn = self.connect()

        sql = f'INSERT INTO {db_Table} (username, timeunix, login_time, server_local_ip, ' \
              f'client_ip, client_trusted_ip, client_trusted_port, logout_time, bytes_received, bytes_sent) VALUES ({value})'

        mysql_cur = mysql_conn.cursor()  # mysql cursor
        try:
            mysql_cur.execute(sql)
            mysql_conn.commit()
        except Exception as e:
            raise ValueError(f'mysql insert failed! {sql}, error: {str(e)}')

        self.close(mysql_cur=mysql_cur, mysql_conn=mysql_conn)

    def select(self, mysql_cur, username):
        sql = f'SELECT id, username, timeunix FROM {db_Table} WHERE username="{username}" ORDER BY  timeunix DESC LIMIT 1'

        try:
            mysql_cur.execute(sql)
        except Exception as e:
            raise ValueError(f'mysql select failed! {sql}, error: {str(e)}')

        result = mysql_cur.fetchone()
        if result is None:
            return None
        return result

    def close(self, mysql_cur, mysql_conn):

        mysql_cur.close()
        mysql_conn.close()


if __name__ == '__main__':
    pass
    # value = f'"wanghuang", 1693882866, "2023-09-05 06:42:00", "111.111.111.111", "111.111.111.111", "111.111.111.111", 342, NULL, NULL, NULL'
    # VNCLogMysql().insert(value=value)
    # VNCLogMysql().update(username='wanghuang', logout_time='2023-09-05 06:50:00', bytes_sent=23, bytes_received=23)
