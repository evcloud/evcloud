#coding=utf-8
from django.conf import settings

from .models import HostErrorLog, VmMigrateLog

class MonitoringAPI(object):

	def get_host_error_log_by_id(self,log_id):
		objs = HostErrorLog.objects.filter(id=log_id)
		if objs.exists():
			return objs.first()
		return None


	def get_host_error_log_list(self,host_id=None,host_ipv4=None,deleted=False):
		log_list = []
		if host_id:
			objs = HostErrorLog.objects.filter(host_id=host_id, deleted=deleted)
		elif host_ipv4:
			objs = HostErrorLog.objects.filter(host_ipv4=host_ipv4, deleted=deleted)
		else:
			objs = HostErrorLog.objects.filter(deleted=deleted)

		if objs.exists():
			log_list = [log for log in objs ]			
		return log_list


	def get_vm_migrate_log_by_id(self,log_id):
		objs = VmMigrateLog.objects.filter(id=log_id)
		if objs.exists():
			return objs.first()
		return None


	def get_vm_migrate_log_list(self,vm_uuid=None,host_error_log_id=None,deleted=False):
		log_list = []
		
		if vm_uuid:
			objs = VmMigrateLog.objects.filter(vm_uuid=vm_uuid,deleted=deleted)
		else:
			objs = VmMigrateLog.objects.filter(deleted=deleted)
		if host_error_log_id:
			objs = objs.filter(host_error_log_id=host_error_log_id)
		if objs.exists():
			log_list = [log for log in objs ]			
		return log_list


	def delete_host_error_log(self,log_id):
		try:
			objs = HostErrorLog.objects.filter(id=log_id)
			if objs.exists():
				objs.update(deleted=True)
			return True
		except Exception as e:
			if settings.DEBUG: raise e		
		return False


	def create_host_error_log(self,host_id,host_ipv4,info=''):
		try:
			obj = HostErrorLog()
			obj.host_id = host_id
			obj.host_ipv4 = host_ipv4
			obj.info = info
			obj.save()
			return obj.id
		except Exception as e:
			if settings.DEBUG: raise e
		return None


	def delete_vm_migrate_log(self,log_id):		
		try:
			objs = VmMigrateLog.objects.filter(id=log_id)
			if objs.exists():
				objs.update(deleted=True)
			return True
		except Exception as e:
			if settings.DEBUG: raise e		
		return False

	def create_vm_migrate_log(self,host_error_log_id,vm_uuid,migrate_res,src_host_ipv4,dst_host_ipv4,info=''):
		try:
			obj = VmMigrateLog()
			obj.host_error_log_id = host_error_log_id 
			obj.vm_uuid = vm_uuid 
			obj.src_host_ipv4 = src_host_ipv4 
			obj.dst_host_ipv4 = dst_host_ipv4 
			obj.migrate_res = migrate_res
			obj.info = info
			obj.save()
			return obj.id
		except Exception as e:
			if settings.DEBUG: raise e
		return None

	