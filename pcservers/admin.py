from django.contrib import admin

from .models import Room, Department, ServerType, PcServer


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'city', 'desc')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'number', 'name')


@admin.register(ServerType)
class ServerTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'desc')


@admin.register(PcServer)
class PcServerAdmin(admin.ModelAdmin):
    list_display = ('host_ipv4', 'ipmi_ip', 'status', 'department', 'user', 'room',
                    'location', 'server_type', 'use_for', 'due_time')
    list_display_links = ('host_ipv4', 'ipmi_ip')
    list_filter = ('room', 'status', 'server_type', 'department', 'user')
    list_select_related = ('room', 'department', 'server_type')
    search_fields = ('host_ipv4', 'location', 'ipmi_ip')