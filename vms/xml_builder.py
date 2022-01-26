from utils import errors
from .xml import XMLEditor


class VmXMLBuilder:
    @staticmethod
    def xml_edit_vcpu(xml_desc: str, vcpu: int):
        """
        修改 xml中vcpu节点内容

        :param xml_desc: 定义虚拟机的xml内容
        :param vcpu: 虚拟cpu数
        :return:
            xml: str    # success

        :raise:  VmError
        """
        xml = XMLEditor()
        if not xml.set_xml(xml_desc):
            raise errors.VmError(msg='xml文本无效')

        root = xml.get_root()
        try:
            root.getElementsByTagName('vcpu')[0].firstChild.data = vcpu
        except Exception as e:
            raise errors.VmError(msg='修改xml文本vcpu节点错误')

        return root.toxml()

    @staticmethod
    def xml_edit_mem(xml_desc: str, mem: int):
        """
        修改xml中mem节点内容

        :param xml_desc: 定义虚拟机的xml内容
        :param mem: 修改内存大小
        :return:
            xml: str    # success

        :raise:  VmError
        """
        xml = XMLEditor()
        if not xml.set_xml(xml_desc):
            raise errors.VmError(msg='xml文本无效')
        try:
            root = xml.get_root()
            node = root.getElementsByTagName('memory')[0]
            node.attributes['unit'].value = 'MiB'
            node.firstChild.data = mem

            node = root.getElementsByTagName('currentMemory')[0]
            node.attributes['unit'].value = 'MiB'
            node.firstChild.data = mem

            return root.toxml()
        except Exception as e:
            raise errors.VmError(msg='修改xml文本memory节点错误')

    def get_vm_vdisk_dev_list(self, xml_desc: str):
        """
        获取虚拟机所有硬盘的dev

        :param xml_desc: 虚拟机xml
        :return:
            (disk:list, dev:list)    # disk = [disk_uuid, disk_uuid, ]; dev = ['vda', 'vdb', ]

        :raises: VmError
        """
        dev_list = []
        disk_list = []
        xml = XMLEditor()
        if not xml.set_xml(xml_desc):
            raise errors.VmError(msg='虚拟机xml文本无效')

        root = xml.get_root()
        devices = root.getElementsByTagName('devices')[0].childNodes
        for d in devices:
            if d.nodeName == 'disk':
                for disk_child in d.childNodes:
                    if disk_child.nodeName == 'source':
                        pool_disk = disk_child.getAttribute('name')
                        disk = pool_disk.split('/')[-1]
                        disk_list.append(disk)
                    if disk_child.nodeName == 'target':
                        dev_list.append(disk_child.getAttribute('dev'))

        return disk_list, dev_list

    @staticmethod
    def new_vdisk_dev(dev_list: list):
        """
        顺序从vda - vdz中获取下一个不包含在dev_list中的的dev字符串

        :param dev_list: 已使用的dev的list
        :return:
            str     # success
            None    # 没有可用的dev了
        """
        # 从vdb开始，系统xml模板中系统盘驱动和硬盘一样为virtio时，硬盘使用vda会冲突错误
        for i in range(1, 26):
            dev = 'vd' + chr(ord('a') + i % 26)
            if dev not in dev_list:
                return dev

        return None

    @staticmethod
    def xml_remove_sys_disk_auth(xml_desc: str):
        """
        去除vm xml中系统盘节点ceph认证的auth

        :param xml_desc: 定义虚拟机的xml内容
        :return:
            xml: str    # success

        :raise:  VmError
        """
        xml = XMLEditor()
        if not xml.set_xml(xml_desc):
            raise errors.VmError(msg='虚拟机xml文本无效')

        root = xml.get_root()
        devices = root.getElementsByTagName('devices')
        if not devices:
            raise errors.VmError(msg='虚拟机xml文本无效, 未找到devices节点')

        disks = devices[0].getElementsByTagName('disk')
        if not disks:
            raise errors.VmError(msg='虚拟机xml文本无效, 未找到devices>disk节点')
        disk = disks[0]
        auth = disk.getElementsByTagName('auth')
        if not auth:
            return xml_desc

        disk.removeChild(auth[0])
        return root.toxml()

    def build_vm_xml_desc(self, vm_uuid: str, mem: int, vcpu: int, vm_disk_name: str, image, mac_ip):
        """
        构建虚拟机的xml
        :param vm_uuid:
        :param mem:
        :param vcpu:
        :param vm_disk_name: vm的系统盘镜像rbd名称
        :param image: 系统镜像实例
        :param mac_ip: MacIP实例
        :return:
            xml: str
        """
        pool = image.ceph_pool
        pool_name = pool.pool_name
        ceph = pool.ceph
        xml_tpl = image.xml_tpl.xml  # 创建虚拟机的xml模板字符串
        xml_desc = xml_tpl.format(name=vm_uuid, uuid=vm_uuid, mem=mem, vcpu=vcpu, ceph_uuid=ceph.uuid,
                                  ceph_pool=pool_name, diskname=vm_disk_name, ceph_username=ceph.username,
                                  ceph_hosts_xml=ceph.hosts_xml, mac=mac_ip.mac, bridge=mac_ip.vlan.br)

        if not ceph.has_auth:
            xml_desc = self.xml_remove_sys_disk_auth(xml_desc)

        return xml_desc
