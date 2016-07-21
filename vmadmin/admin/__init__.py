#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2015-10-23
#@desc:    此模块用于对django admin的site和admin类进行修改，
#          统一修改后台管理所使用的template
########################################################################

from django.contrib import admin

admin_site = admin.site

admin_site.login_form = None
admin_site.index_template = 'admin/vm_index.html'
admin_site.app_index_template = 'admin/vm_app_index.html'
admin_site.login_template = None
admin_site.logout_template = None
admin_site.password_change_template = None
admin_site.password_change_done_template = None

from compute.models import Center, Group, Host, Vm, VmArchive
from .compute_admin import CenterAdmin, GroupAdmin, HostAdmin, VmAdmin, VmArchiveAdmin
admin_site.register(Center, CenterAdmin)
admin_site.register(Group, GroupAdmin)
admin_site.register(Host, HostAdmin)
admin_site.register(Vm, VmAdmin)
admin_site.register(VmArchive, VmArchiveAdmin)

from image.models import ImageType, Image, Xml
from .image_admin import ImageTypeAdmin, ImageAdmin, XmlAdmin
admin_site.register(ImageType, ImageTypeAdmin)
admin_site.register(Image, ImageAdmin)
admin_site.register(Xml, XmlAdmin)

from network.models import VlanType, Vlan, MacIP
from .network_admin import VlanTypeAdmin, VlanAdmin, MacIPAdmin
admin_site.register(VlanType, VlanTypeAdmin)
admin_site.register(Vlan, VlanAdmin)
admin_site.register(MacIP, MacIPAdmin)

from storage.models import CephHost, CephPool
from .storage_admin import CephHostAdmin, CephPoolAdmin
admin_site.register(CephHost, CephHostAdmin)
admin_site.register(CephPool, CephPoolAdmin)

from django.contrib.auth.models import User, Group
from .auth_admin import VMUserAdmin, VMGroupAdmin
admin_site.unregister(User)
admin_site.unregister(Group)
admin_site.register(User, VMUserAdmin)
admin_site.register(Group, VMGroupAdmin)

from api.models import Log
from .api_admin import LogAdmin
admin_site.register(Log, LogAdmin)

from device.models import DBGPU
from .device_admin import DBGPUAdmin
admin_site.register(DBGPU, DBGPUAdmin)


from volume.models import DBCephVolume
from volume.models import DBCephQuota
from .volume_admin import CephVolumeAdmin
from .volume_admin import CephQuotaAdmin
admin_site.register(DBCephVolume, CephVolumeAdmin)
admin_site.register(DBCephQuota, CephQuotaAdmin)


from django.contrib.auth.models import Group
admin_site.unregister(Group)