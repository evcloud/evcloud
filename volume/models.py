#coding=utf-8
from django.db import models
from django.contrib.auth.models import User
from storage.models import CephPool
from compute.models import Group

class AbsDBVolume(models.Model):
	'''附加磁盘抽象类'''
	class Meta:
		abstract = True
	
	uuid = models.CharField(max_length=200, primary_key=True)
	user = models.ForeignKey(User, null=True, blank=True)
	group = models.ForeignKey(Group, null=True, blank=True)
	creator = models.CharField(max_length=200, null=True, blank=True)
	create_time = models.DateTimeField(auto_now_add=True)
	size = models.IntegerField()
	remarks = models.TextField(null=True, blank=True)
	vm = models.CharField(max_length=200, null=True, blank=True)
	dev = models.CharField(max_length=100, null=True, blank=True)

class DBCephVolume(AbsDBVolume):
	'''ceph块'''
	cephpool = models.ForeignKey(CephPool)


class DBCephQuota(models.Model):
	group_id = models.IntegerField(null=True, blank=True, unique=True)
	total_size = models.IntegerField()
	max_volume_size = models.IntegerField()
	min_volume_size = models.IntegerField()

class DBVolumeMountLog(models.Model):
	operate_type_list = (
		(1, 'MOUNT'),
		(2, 'UMOUNT')
		)
	operate_user = models.CharField(max_length=200)
	operate_time = models.DateTimeField(auto_now_add=True)
	operate_type = models.IntegerField(choices=operate_type_list)
	vmid = models.CharField(max_length=200)
	volume_id = models.CharField(max_length=200)
	volume_type = models.CharField(max_length=50)
