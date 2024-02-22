import subprocess


class HosthardwareInfo:

    def __init__(self, ipv4, ssh_key):
        self.ipv4 = ipv4
        self.ssh_key = ssh_key

    def get_hugepages(self):
        """获取大页内存"""

        ip = f'{self.ipv4}'
        key = f'{self.ssh_key}'

        line = ['ssh', '-i', key, ip, 'cat /proc/meminfo  | grep -E "HugePages_Total|HugePages_Free"']

        try:
            p = subprocess.check_output(line, stderr=subprocess.STDOUT, timeout=5)
        except subprocess.TimeoutExpired as time_e:
            raise ValueError(f'{time_e}')
        except subprocess.CalledProcessError as call_e:
            raise ValueError(f'{call_e.output.decode(encoding="utf-8")}')

        p = p.decode(encoding="utf-8").split('\n')

        d = {}
        for i in p:
            if not i:
                break
            men = i.split(':      ')   # ['HugePages_Total', ' 0'] ['HugePages_Free', '  0']
            d[men[0]] = men[1].strip()

        return d

    def get_cpu(self):
        # cat /proc/cpuinfo | grep "physical id" | sort | uniq | wc -l

        ip = f'{self.ipv4}'
        key = f'{self.ssh_key}'

        line = ['ssh', '-i', key, ip, 'cat /proc/cpuinfo  | grep "physical id" | sort | uniq | wc -l']

        try:
            p = subprocess.check_output(line, stderr=subprocess.STDOUT, timeout=3)
        except subprocess.TimeoutExpired as time_e:
            raise ValueError(f'{time_e}')
        except subprocess.CalledProcessError as call_e:
            raise ValueError(f'{call_e.output.decode(encoding="utf-8")}')

        p = p.decode(encoding="utf-8").split('\n')

        if p:
            return p[0]

        return 0