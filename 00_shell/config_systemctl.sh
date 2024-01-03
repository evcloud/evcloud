#cp /home/uwsgi/evcloud/evcloud.service /usr/lib/systemd/system/ -f
#cp /home/uwsgi/evcloud/evcloud-vnc.service /usr/lib/systemd/system/ -f
#systemctl daemon-reload
#systemctl enable evcloud
#systemctl enable evcloud-vnc

systemctl disable evcloud
systemctl disable evcloud_vnc
systemctl disable evcloud-vnc  # 后期删除

rm /usr/lib/systemd/system/evcloud.service -f
rm /usr/lib/systemd/system/evcloud-vnc.service -f
rm /usr/lib/systemd/system/evcloud_vnc.service -f

ln -s /home/uwsgi/evcloud/00_shell/evcloud.service /usr/lib/systemd/system/evcloud.service
ln -s /home/uwsgi/evcloud/00_shell/evcloud_vnc.service /usr/lib/systemd/system/evcloud_vnc.service

systemctl daemon-reload
systemctl enable evcloud
systemctl enable evcloud_vnc
