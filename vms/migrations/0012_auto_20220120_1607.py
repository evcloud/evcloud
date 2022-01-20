# Generated by Django 3.2.5 on 2022-01-20 08:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vms', '0011_auto_20210726_1557'),
    ]

    operations = [
        migrations.AddField(
            model_name='vm',
            name='sys_disk_size',
            field=models.IntegerField(default=0, help_text='系统盘大小不能小于image大小', verbose_name='系统盘大小(Gb)'),
        ),
        migrations.AddField(
            model_name='vmarchive',
            name='sys_disk_size',
            field=models.IntegerField(default=0, help_text='系统盘大小不能小于image大小', verbose_name='系统盘大小(Gb)'),
        ),
    ]
