#coding=utf-8
from django.core.management.base import BaseCommand 
from ...tools import DeviceTool
from ...api import GPUAPI
from compute.api import HostAPI

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('gpu_address', type=str)

    def handle(self, *args, **options):
        address = options['gpu_address']

        api = GPUAPI()
        gpu = api.get_gpu_by_address(address)
        res = api.umount(gpu.id)
        print(res)