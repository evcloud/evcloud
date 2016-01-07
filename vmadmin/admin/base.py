#coding=utf-8
from django.contrib import admin

class VMModelAdmin(admin.ModelAdmin):
    add_form_template = 'admin/vm_change_form.html'
    change_form_template = 'admin/vm_change_form.html'
    change_list_template = 'admin/vm_change_list.html'
    delete_confirmation_template = None
    delete_selected_confirmation_template = None
    object_history_template = None