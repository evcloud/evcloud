from django.core.management.base import BaseCommand, CommandError

from ceph.models import GlobalConfig


class Command(BaseCommand):
    '''
    检测/添加全局配置参数
    '''
    error_buckets = []

    help = """ 
            检测/添加全局配置参数
            python manage.py check_global_config
           """

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        print(options)

        admin = GlobalConfig.objects.filter(name='resourceAdministrator').first()
        if admin:
            admin.name = 'resourceAdmin'
            admin.save()

        try:
            GlobalConfig().initial_site_parameter()
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"error check global config:{self.error_buckets}"))

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully check global config.'
            )
        )
