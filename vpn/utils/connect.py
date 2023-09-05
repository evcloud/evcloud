import os
import sys
import time
sys.path.append('/home/uwsgi/evcloud/vpn')

from mysqlconnect import VNCLogMysql
from log import get_logger

log = get_logger('vpn_login')


def get_environ_value():
    try:
        username = os.environ['common_name']
        timeunix = os.environ['time_unix']  # 时间戳、登录时间

        server_local_ip = os.environ['ifconfig_local']  # 服务端地址
        client_ip = os.environ['ifconfig_pool_remote_ip']  # 客户端地址
        client_trusted_ip = os.environ['trusted_ip']  # 客户端公网IP地址
        client_trusted_port = os.environ['trusted_port']  # 客户端公网IP地址端口

        login_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    except Exception as e:
        log.error(f'无法重vpn获取当前的参数， error:{str(e)}')
        return
    return {'username': username, 'timeunix': timeunix, 'server_local_ip': server_local_ip, 'client_ip': client_ip,
            'client_trusted_ip': client_trusted_ip, 'client_trusted_port': client_trusted_port,
            'login_time': login_time}


def main():
    k = get_environ_value()
    value = f'"{k["username"]}", {k["timeunix"]}, "{k["login_time"]}", "{k["server_local_ip"]}", "{k["client_ip"]}", "{k["client_trusted_ip"]}", ' \
            f'{k["client_trusted_port"]}, NULL, NULL, NULL'

    try:
        VNCLogMysql().insert(value=value)
    except Exception as e:
        log.error(f'vpn用户 {k["username"]} -->登录时间：{k["login_time"]}, 登录时错误：{str(e)}')

    log.info(
        f'vpn用户 {k["username"]} --> 登录时间：{k["login_time"]}, 客户端IP地址：{k["client_ip"]}, 服务端IP地址：{[k["server_local_ip"]]},'
        f'客户端使用的公网IP地址及端口：{k["client_trusted_ip"]}:{k["client_trusted_port"]}')


if __name__ == '__main__':
    os.environ['common_name'] = 'wanghuang'
    os.environ['time_unix'] = '1693882866'
    os.environ['ifconfig_local'] = '10.10.10.10'
    os.environ['ifconfig_pool_remote_ip'] = '192.168.192.111'
    os.environ['trusted_ip'] = '111.111.111.111'
    os.environ['trusted_port'] = '232'
    main()
