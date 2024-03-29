# Generated by Django 3.2.13 on 2022-09-19 08:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compute', '0006_auto_20220713_1929'),
    ]

    operations = [
        migrations.AlterField(
            model_name='host',
            name='enable',
            field=models.BooleanField(default=True, verbose_name='启用宿主机'),
        ),
        migrations.AlterField(
            model_name='host',
            name='mem_allocated',
            field=models.IntegerField(default=0, verbose_name='虚拟机已用内存(Gb)'),
        ),
        migrations.AlterField(
            model_name='host',
            name='mem_total',
            field=models.IntegerField(default=30, verbose_name='虚拟机可用内存总量(Gb)'),
        ),
        migrations.AlterField(
            model_name='host',
            name='vm_created',
            field=models.IntegerField(default=0, verbose_name='本地已创建虚拟机数量'),
        ),
        migrations.AlterField(
            model_name='host',
            name='vm_limit',
            field=models.IntegerField(default=10, verbose_name='本地虚拟机数量上限'),
        ),
    ]
