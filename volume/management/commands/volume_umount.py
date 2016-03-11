#coding=utf-8
from django.core.management.base import BaseCommand 
from ...api import CephVolumeAPI

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('volume_id', type=str)

    def handle(self, *args, **options):
        volume_id = options['volume_id']
        api = CephVolumeAPI()
        print(api.umount(volume_id))