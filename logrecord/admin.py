from django.contrib import admin

from logrecord.models import LogRecord


# Register your models here.


@admin.register(LogRecord)
class LogRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'resourc_type', 'action_flag', 'operation_content', 'method', 'full_path', 'message', 'username', 'create_time')

