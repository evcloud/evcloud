#coding=utf-8
from django.core.management.base import BaseCommand 
from ...api import VolumeAPI

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('volume_id', type=str)
        parser.add_argument('size', type=int)

    def handle(self, *args, **options):
        volume_id = options['volume_id']
        size = options['size']
        api = VolumeAPI()
        print(api.resize(volume_id, size))