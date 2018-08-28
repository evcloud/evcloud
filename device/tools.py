#coding=utf-8
from compute.manager import VirtManager

class DeviceTool(VirtManager):
	def get_device_list(self, host_ipv4, cap=None):
		conn = self._connection(host_ipv4)
		return conn.listDevices(cap)