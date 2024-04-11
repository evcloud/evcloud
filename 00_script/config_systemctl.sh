#cp /home/uwsgi/evcloud/evcloud.service /usr/lib/systemd/system/ -f
#cp /home/uwsgi/evcloud/evcloud_vnc.service /usr/lib/systemd/system/ -f
#systemctl daemon-reload
#systemctl enable evcloud
#systemctl enable evcloud_vnc

systemctl disable evcloud
systemctl disable evcloud_vnc
systemctl disable evcloud-vnc  # 后期删除
systemctl disable openvpn.service

rm /usr/lib/systemd/system/evcloud.service -f
rm /usr/lib/systemd/system/evcloud-vnc.service -f
rm /usr/lib/systemd/system/evcloud_vnc.service -f

ln -s /home/uwsgi/evcloud/00_script/evcloud.service /usr/lib/systemd/system/evcloud.service
ln -s /home/uwsgi/evcloud/00_script/evcloud_vnc.service /usr/lib/systemd/system/evcloud_vnc.service
ln -s /home/uwsgi/evcloud/00_script/openvpn.service /usr/lib/systemd/system/openvpn.service

# 如果 软连接不生效 将 软连接命令注释掉 将下面两行内容打开 重新执行该文件
#cp /home/uwsgi/evcloud/00_script/evcloud.service /usr/lib/systemd/system/ -f
#cp /home/uwsgi/evcloud/00_script/evcloud_vnc.service /usr/lib/systemd/system/ -f

systemctl daemon-reload
systemctl enable evcloud
systemctl enable evcloud_vnc
systemctl enable openvpn.service
