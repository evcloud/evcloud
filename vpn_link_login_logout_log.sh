ln -s /etc/openvpn/server/connect.py /home/uwsgi/evcloud/vpn/connect.py
ln -s /etc/openvpn/server/disconnect.py /home/uwsgi/evcloud/vpn/disconnect.py


client-connect  /etc/openvpn/server/connect.py
client-disconnect  /etc/openvpn/server/disconnect.py