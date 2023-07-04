# Generated by Django 2.2.7 on 2019-12-02 02:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vms', '0004_vmdisksnap'),
        ('compute', '0003_auto_20191101_1024'),
        ('device', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PCIDevice',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('type', models.SmallIntegerField(choices=[(0, '未知设备'), (1, 'GPU')], default=0, verbose_name='设备类型')),
                ('attach_time', models.DateTimeField(blank=True, null=True, verbose_name='挂载时间')),
                ('enable', models.BooleanField(default=True, verbose_name='状态')),
                ('remarks', models.TextField(blank=True, null=True, verbose_name='备注')),
                ('address', models.CharField(help_text='format:[domain]:[bus]:[slot]:[function], example: 0000:84:00:0 或 /dev/sdp 本地盘', max_length=100)),
                ('host', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pci_devices', to='compute.Host', verbose_name='宿主机')),
                ('vm', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='device_set', to='vms.Vm', verbose_name='挂载于虚拟机')),
            ],
            options={
                'verbose_name': 'PCIe设备',
                'verbose_name_plural': 'PCIe设备',
                'ordering': ['-id'],
            },
        ),
        migrations.DeleteModel(
            name='Device',
        ),
        migrations.DeleteModel(
            name='DeviceType',
        ),
    ]
