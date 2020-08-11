#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
import traceback
import MySQLdb

logging.basicConfig(level=logging.WARNING, filename='/var/log/nginx/openvpn-auth.log', filemode='a')  # 'a'为追加模式,'w'为覆盖写


def return_auth_failed():
    sys.exit(1)  # 认证未通过


def return_auth_passed():
    sys.exit(0)  # 认证通过


try:
    # 将项目路径添加到系统搜寻路径当中，查找方式为从当前脚本开始，找到要调用的django项目的路径
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    # 设置项目的配置文件 不做修改的话就是 settings 文件
    from django_site.security import DATABASES
except Exception as e:
    logging.error(traceback.format_exc())
    return_auth_failed()


def get_vpn(username):
    d = DATABASES.get('default')
    conn = MySQLdb.connect(host=d['HOST'],
                           user=d['USER'],
                           password=d['PASSWORD'],
                           database=d['NAME'],
                           port=int(d['PORT']))
    c = conn.cursor(MySQLdb.cursors.DictCursor)
    c.execute("SELECT username, password, active FROM vpn_auth WHERE username=%s", (username,))
    vpn = c.fetchone()
    c.close()
    conn.close()

    return vpn


def auth(username, raw_password):
    """
    :param username:
    :param raw_password:
    :return:
        True -> auth passed
        False -> not passed
    """
    # 验证用户
    try:
        vpn = get_vpn(username=username)
    except Exception as exc:
        msg = traceback.format_exc()
        logging.error(msg)
        return False

    if not vpn:
        return False

    if not vpn['active']:
        return False

    if vpn['password'] == raw_password:
        return True

    return False


if __name__ == '__main__':
    username = os.environ.get('username', None)
    password = os.environ.get('password', None)
    time_string = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

    if username is None or password is None:
        logging.error(f'time: {time_string},error!username={username}, password={password}.')
        return_auth_failed()

    if not auth(username=username, raw_password=password):
        logging.warning(f'time: {time_string},auth failed.username={username}')
        return_auth_failed()    # 认证未通过
    else:
        logging.warning(f'time: {time_string},auth OK!username={username}')
        return_auth_passed()
