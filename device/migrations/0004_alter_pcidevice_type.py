# Generated by Django 3.2.13 on 2023-02-03 00:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('device', '0003_alter_pcidevice_enable'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pcidevice',
            name='type',
            field=models.SmallIntegerField(choices=[(0, '未知设备'), (1, 'GPU'), (2, '网卡')], default=0, verbose_name='资源类型'),
        ),
    ]
