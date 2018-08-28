#coding=utf-8
from django.core.management.base import BaseCommand 
from ...api import VolumeAPI

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('vm_uuid', type=str)
        parser.add_argument('volume_id', type=str)

    def handle(self, *args, **options):
        volume_id = options['volume_id']
        vm_id = options['vm_uuid']
        api = VolumeAPI()
        print(api.mount(vm_id, volume_id))