#codign=utf-8
from .base import VMModelAdmin
from vmadmin.models import *

class SiteConfigAdmin(VMModelAdmin):
    list_display = ('name','pro_enable')
