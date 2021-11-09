# Generated by Django 3.2.5 on 2021-07-26 07:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vms', '0010_auto_20210615_1634'),
    ]

    operations = [
        migrations.AddField(
            model_name='vm',
            name='disk_type',
            field=models.CharField(choices=[('ceph-rbd', 'Ceph rbd'), ('local', '本地硬盘')], default='ceph-rbd', max_length=16, verbose_name='系统盘类型'),
        ),
        migrations.AddField(
            model_name='vmarchive',
            name='disk_type',
            field=models.CharField(choices=[('ceph-rbd', 'Ceph rbd'), ('local', '本地硬盘')], default='ceph-rbd', max_length=16, verbose_name='系统盘类型'),
        ),
    ]