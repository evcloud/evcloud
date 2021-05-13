cp /home/uwsgi/evcloud/evcloud.service /usr/lib/systemd/system/ -f
cp /home/uwsgi/evcloud/evcloud-vnc.service /usr/lib/systemd/system/ -f
systemctl daemon-reload
systemctl enable evcloud
systemctl enable evcloud-vnc
