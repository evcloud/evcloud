from django.contrib.auth.admin import UserAdmin, GroupAdmin
from .base import VMModelAdmin

class VMUserAdmin(UserAdmin, VMModelAdmin):
    pass

class VMGroupAdmin(GroupAdmin, VMModelAdmin):
    pass