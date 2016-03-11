#coding=utf-8
from django.core.management.base import BaseCommand 
from ...api import CephVolumeAPI

class Command(BaseCommand):
    # def add_arguments(self, parser):
    #     parser.add_argument('vlan_id', type=int)
    #     parser.add_argument('start_ip', type=str)
    #     parser.add_argument('num', type=int)

    def handle(self, *args, **options):
        api = CephVolumeAPI()
        for v in api.get_volume_list():
            print(v.id, v.size, v.vm, v.attach_time)

