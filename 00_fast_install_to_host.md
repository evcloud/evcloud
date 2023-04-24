1. 准备 Linux LiveCD 光盘（例如： https://download.fedoraproject.org/pub/fedora/linux/releases/38/Workstation/x86_64/iso/Fedora-Workstation-Live-x86_64-38-1.6.iso）
2. 从 LiveCD 引导启动主机（如果是EFI，需要关闭security选项）。进入系统，切换到root用户
3. 设置主机网络，需连接至公网
4. 在主机系统，打开终端执行：  rsync -avP evcloud.cstcloud.cn::AutoInstall/* /root/
5. 检查设备信息，确定系统要安装的目的磁盘（例如 /dev/sda ）
6. 编辑/root/20_install.cfg文件，将disk参数值修改为上一步确定的 /dev/sda，其它参数可根据注释的说明及需求相应调整
7. 执行系统部署程序： python3 /root/11_install_bios_uefi_grub4dos_v20230303.py
8. 执行完毕后重启即可（需要设置 /dev/sda为启动盘）
