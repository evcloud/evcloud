#!/usr/bin/python
import os
import sys
import time

sys.path.insert(0, '/home/uwsgi/evcloud/vpn/utils')

from log import get_logger
from mysqlconnect import VNCLogMysql

log = get_logger('vpn_logout')


def get_environ_value():
    try:
        bytes_received = os.environ['bytes_received']  # 上行流量
        bytes_sent = os.environ['bytes_sent']  # 下行流量
        timeunix = os.environ['time_unix']  # 登出时间
        username = os.environ['common_name']

        logout_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    except Exception as e:
        log.error(f'无法重vpn获取当前的参数， error:{str(e)}')
        return
    return {'username': username, 'timeunix': timeunix, 'bytes_sent': bytes_sent, 'bytes_received': bytes_received,
            'logout_time': logout_time}


def main():
    k = get_environ_value()
    try:
        VNCLogMysql().update(username=k['username'], logout_time=k['logout_time'], bytes_sent=k['bytes_sent'],
                             bytes_received=k['bytes_received'])
    except Exception as e:
        log.error(f'vpn用户 {k["username"]} -->登出时间：{k["logout_time"]}, 登出时错误：{str(e)}')

    log.info(f'vpn用户 {k["username"]} --> 登出时间：{k["logout_time"]}, 客户端接收：{k["bytes_sent"]}, 客户端发送：{k["bytes_received"]}')


if __name__ == '__main__':
    os.environ['common_name'] = 'wanghuang'
    os.environ['time_unix'] = '1693882866'
    os.environ['bytes_sent'] = '23'
    os.environ['bytes_received'] = '234'
    main()
