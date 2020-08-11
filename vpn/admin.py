from django.contrib import admin
from .models import VPNAuth


@admin.register(VPNAuth)
class VPNAuthAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'password', 'active', 'create_time', 'create_user', 'modified_time',
                    'modified_user', 'remarks']
    list_display_links = ['id', 'username']
    search_fields = ['username', 'remarks']
