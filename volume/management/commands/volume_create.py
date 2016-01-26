#coding=utf-8
from django.core.management.base import BaseCommand 
from ...api import CephVolumeAPI

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('cephpool_id', type=int)
        parser.add_argument('size', type=int)

    def handle(self, *args, **options):
        cephpool_id = options['cephpool_id']
        size = options['size']
        api = CephVolumeAPI()
        print(api.create(cephpool_id, size))