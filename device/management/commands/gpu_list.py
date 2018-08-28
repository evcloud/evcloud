#coding=utf-8
from django.core.management.base import BaseCommand 
from ...tools import DeviceTool
from ...api import GPUAPI
from compute.api import HostAPI

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('host_ip', type=str, default=None)

    def handle(self, *args, **options):
        host_ip = options['host_ip']
        host_api = HostAPI()
        host = host_api.get_host_by_ipv4(host_ip)
        api = GPUAPI()
        gpu_list = api.get_gpu_list_by_host_id(host.id)
        for gpu in gpu_list:
            print(gpu.host_ipv4, gpu.address, gpu.vm)