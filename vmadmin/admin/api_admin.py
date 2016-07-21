#codign=utf-8
from .base import VMModelAdmin
from compute.models import *

class LogAdmin(VMModelAdmin):
    list_display = ('user', 'op', 'start_time', 'finish_time', 'result', 'error', 'from_trd_part', 'args')
    list_filter = [ 'result', 'from_trd_part','op','user']
    ordering = ('-start_time',)
    readonly_fields = ('user', 'op', 'start_time', 'finish_time', 'result', 'error', 'from_trd_part', 'args')
    search_fields = ('error', 'args')
    list_display_links = ()
    
    def has_add_permission(self, request):
        return False
    
#     def has_change_permission(self, request, obj=None):
#         return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    actions_on_top = False
    actions_on_bottom = False
    actions_selection_counter = False