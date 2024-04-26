from django.contrib import admin

from logrecord.models import LogRecord


# Register your models here.


@admin.register(LogRecord)
class LogRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'operation_content', 'method', 'full_path', 'message',  'create_time')

