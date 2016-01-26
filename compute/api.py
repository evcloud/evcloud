#coding=utf-8
from .models import Center as DBCenter
from .models import Group as DBGroup
from .models import Vm as DBVm
from .models import Host as DBHost
from .center import Center
from .group import Group
from vmuser.api import API as UserAPI
from .vm.vm import VM

from api.error import Error
from api.error import ERR_VM_ID
from api.error import ERR_HOST_ID
from api.error import ERR_HOST_IPV4
from .host.manager import HostManager
from .host.host import Host

class CenterAPI(object):

    def center_id_exists(self, center_id):
        return DBCenter.objects.filter(pk=center_id).exists()

    def get_center_by_id(self, center_id):
        center = DBCenter.objects.filter(id = center_id)
        if not center.exists():
            return False
        center = center[0]
        return self._get_center_data(center)

    def get_center_list(self):
        centers = DBCenter.objects.all().order_by('order')
        ret_list = []
        for center in centers:
            ret_list.append(self._get_center_data(center))
        return ret_list

    def _get_center_data(self, center):
        if type(center) != DBCenter:
            return False
        return Center(center)


class GroupAPI(object):

    def __init__(self, user_api=None):
        if not user_api:
            self.user_api = UserAPI()
        else:
            self.user_api = user_api

    def get_groups_in_perm(self, username, center_id = None):
        user = self.user_api.get_db_user_by_username(username)
        if self.user_api.is_superuser(user):
            if center_id == None:
                groups = DBGroup.objects.all()
            else:
                groups = DBGroup.objects.filter(center_id = center_id)
        else:
            if center_id == None:
                groups = DBGroup.objects.filter(admin_user = user)
            else:
                groups = DBGroup.objects.filter(admin_user = user, center_id = center_id)
        groups = groups.order_by('order')
        ret_list = []
        for group in groups:
            ret_list.append(_get_group_data(group))
        return ret_list

    def get_group(self, group_id):
        group = DBGroup.objects.filter(id = group_id)
        if not group.exists():
            return False
        return _get_group_data(group[0])

            
    def has_center_perm(self, username, center_id):
        user = self._get_user_db_by_username(username)
        '''对指定center有部分或全部管理权，即对该分中心中的 某个集群有管理权,则返回True'''
        return DBGroup.objects.filter(admin_user = user, center_id = center_id).exists()


    #--------------------------------------------------------
    def _get_group_data(group):
        if not type(group) == DBGroup:
            return False
        return Group(group)

class VmAPI(object):
    def __init__(self, user_api=None):
        if not user_api:
            self.user_api = UserAPI()
        else:
            self.user_api = user_api

    def get_vm_by_uuid(self, vm_uuid):
        vm = DBVm.objects.filter(uuid = vm_uuid)
        if not vm.exists():
            raise Error(ERR_VM_ID)
        return VM(vm[0])

    def vm_uuid_exists(self, vm_uuid):
        vm = DBVm.objects.filter(uuid = vm_uuid)
        return vm.exists()
        
    def attach_device(self, vm_uuid, xml):
        vm = self.get_vm_by_uuid(vm_uuid)
        return vm.attach_device(xml)

    def detach_device(self, vm_uuid, xml):
        vm = self.get_vm_by_uuid(vm_uuid)
        return vm.detach_device(xml)       

class HostAPI(object):
    def __init__(self, user_api=None, manager=None):
        if not user_api:
            self.user_api = UserAPI()
        else:
            self.user_api = user_api
        if not manager:
            self.manager = HostManager()
        else:
            self.manager = manager

    def get_host_by_id(self, host_id):
        db = DBHost.objects.filter(id = host_id)
        if not db.exists():
            raise Error(ERR_HOST_ID)
        return Host(db[0])

    def get_host_by_ipv4(self, host_ipv4):
        db = DBHost.objects.filter(ipv4 = host_ipv4)
        if not db.exists():
            raise Error(ERR_HOST_IPV4)
        return Host(db[0])

    def get_pci_device_list_from_host(self, host_ip):
        host = self.get_host_by_ipv4(host_ip)
        return host.get_pci_device_list()