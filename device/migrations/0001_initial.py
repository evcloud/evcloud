# Generated by Django 2.2.6 on 2019-10-16 03:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('compute', '0001_initial'),
        ('vms', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeviceType',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='类型名称')),
            ],
            options={
                'verbose_name': '本地资源',
                'verbose_name_plural': '02_本地资源',
            },
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('address', models.CharField(help_text='format:<domain>:<bus>:<slot>:<function>, example: 0000:84:00:0', max_length=100)),
                ('attach_time', models.DateTimeField(blank=True, null=True)),
                ('enable', models.BooleanField(default=True)),
                ('remarks', models.TextField(blank=True, null=True)),
                ('host', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='compute.Host')),
                ('type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='device.DeviceType', verbose_name='类型')),
                ('vm', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='vms.Vm')),
            ],
            options={
                'verbose_name': '本地资源',
                'verbose_name_plural': '01_本地资源',
            },
        ),
    ]
