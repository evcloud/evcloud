import shutil
import os
import stat

shutil.copy('/home/uwsgi/evcloud/vpn/utils/connect.py', '/etc/openvpn/server/connect.py')
shutil.copy('/home/uwsgi/evcloud/vpn/utils/disconnect.py', '/etc/openvpn/server/disconnect.py')

os.chmod('/etc/openvpn/server/connect.py', stat.S_IXUSR + stat.S_IWUSR + stat.S_IRUSR)
os.chmod('/etc/openvpn/server/disconnect.py', stat.S_IXUSR + stat.S_IWUSR + stat.S_IRUSR)


def main(file):
    with open(file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for index, line in enumerate(lines):
        if line.startswith('client-connect'):
            lines[index] = ''

        if line.startswith('client-disconnect'):
            lines[index] = ''

    with open(file, 'w', encoding='utf-8') as fw:
        fw.writelines(lines)
        fw.write('client-connect  /etc/openvpn/server/connect.py \n')
        fw.write('client-disconnect  /etc/openvpn/server/disconnect.py \n')


if __name__ == '__main__':
    main('/etc/openvpn/server/server.conf')
