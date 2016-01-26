#coding=utf-8
from django.core.management.base import BaseCommand 
from ...tools import DeviceTool

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('host_ip', type=str, default=None)
        parser.add_argument('cap', type=str, default=None)

    def handle(self, *args, **options):
        cap = options['cap']
        host = options['host_ip']
        tool = DeviceTool()
        for p in tool.get_device_list(host, cap):
            print(p)
