#coding=utf-8
from django.core.management.base import BaseCommand 

# from network.models import MacIP
from network.models import Vlan, MacIP

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('vlan_id', type=int)
        parser.add_argument('start_ip', type=str)
        parser.add_argument('num', type=int)
            
    def handle(self, *args, **options):
        vlan_id = options['vlan_id']
        start_ip = options['start_ip']
        num = options['num']

        try:
            vlan = Vlan.objects.get(pk = vlan_id)
        except:
            print('vlan_id error.')
            return

        start_ip_int = self._ip_str2int(start_ip)
        if not start_ip_int:
            print('start_ip error.')
            return False

        mac_ip_list = []
        for i in range(num):
            ip_int = start_ip_int + i
            strip = self._ip_int2str(ip_int)
            mac = self._get_mac(ip_int)
            print(strip, mac)
            macip = MacIP()
            macip.vlan_id = vlan_id
            macip.mac = mac
            macip.ipv4 = strip
            macip.enable = True
            macip.save()
            mac_ip_list.append((mac, strip, ip_int))
        self._write_dhcpd(vlan, mac_ip_list, 'dhcp_conf_' + start_ip + '[' + str(num) + '].conf')

    #查询数据库，生成dhcpd.conf 文件
    def _write_dhcpd(self, vlan, mac_ip_list, filename):
        fileobj= open(filename, 'w')
        #写入配置项
        lines='subnet %s netmask %s {\n'%(vlan.subnetip,vlan.netmask)
        lines=lines+'\t'+'option routers\t%s;\n' % vlan.gateway
        liens=lines+'\t'+'option subnet-mask\t%s;\n'% vlan.netmask
        lines=lines+'\t'+'option domain-name-servers\t%s;\n' % vlan.dnsserver
        lines=lines+'\t'+'option domain-name-servers\t8.8.8.8;\n'
        lines=lines+'\t'+'option time-offset\t-18000; # EAstern Standard Time\n'
        lines=lines+'\t'+'range dynamic-bootp %s %s;\n' %(mac_ip_list[0][1], mac_ip_list[-1][1])
        lines=lines+'\t'+'default-lease-time 21600;\n'
        lines=lines+'\t'+'max-lease-time 43200;\n'
        lines=lines+'\t'+'next-server 159.226.50.246;   #tftp server\n'
        lines=lines+'\t'+'filename "/pxelinux.0";    #boot file\n'
        fileobj.write(lines)
        
        for i in mac_ip_list:
            line='\t'+'host %s{hardware ethernet %s;fixed-address %s;}\n'%('v_' + str(i[2]) ,i[0],i[1])
            fileobj.write(line)
        fileobj.write('}') #写入最后的‘}’
        fileobj.flush();
        fileobj.close();

    def _get_mac(self, intip):
        mac_list = []
        while True:
            m = intip & 0xF
            if m == 10:
                n = 'A'
            elif m == 11:
                n = 'B'
            elif m == 12:
                n = 'C'
            elif m == 13:
                n = 'D'
            elif m == 14:
                n = 'E'
            elif m == 15:
                n = 'F'
            else:
                n = str(m)
            mac_list.append(n)
            intip  = intip >> 4
            if intip <= 0:
                break
            
        mac_list.reverse()
        mac = 'C8' + ('0000000000' + ''.join(mac_list))[-10:]
        ret = []
        for i in range(0,12,2):
            ret.append(mac[i:i+2])
        return ':'.join(ret)

    def _ip_str2int(self, strip):
        if not type(strip) == str:
            return False
        ip_list = strip.split('.')
        if not len(ip_list) == 4:
            return False
        i = 0
        int_ip = 0
        while True:
            if not ip_list[i].isdigit():
                return False
            int_ip += int(ip_list[i])
            if i >= 3:
                break
            int_ip = int_ip << 8
            i += 1
        return int_ip

    def _ip_int2str(self, intip):
        ip_list = []
        i=0
        while i <3:
            ip_list.append(str(intip % 256))
            intip = intip >> 8
            i += 1
        ip_list.append(str(intip))
        ip_list.reverse()
        return '.'.join(ip_list)