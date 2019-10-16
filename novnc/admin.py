from django.contrib import admin
from .models import Token

class TokenAdmin(admin.ModelAdmin):
    list_display = ('token','ip','port','updatetime')

