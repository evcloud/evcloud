# Generated by Django 3.2.13 on 2023-07-27 06:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0009_alter_macip_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='vlan',
            name='dhcp_config_v6',
            field=models.TextField(blank=True, default=None, null=True, verbose_name='DHCP6部分配置信息'),
        ),
        migrations.AddField(
            model_name='vlan',
            name='dns_server_v6',
            field=models.CharField(blank=True, default=None, max_length=255, null=True, verbose_name='DNS服务IP(IPv6)'),
        ),
        migrations.AddField(
            model_name='vlan',
            name='gateway_v6',
            field=models.GenericIPAddressField(blank=True, default=None, null=True, verbose_name='网关(IPv6)'),
        ),
        migrations.AddField(
            model_name='vlan',
            name='net_mask_v6',
            field=models.GenericIPAddressField(blank=True, default=None, null=True, verbose_name='子网掩码(IPv6)'),
        ),
        migrations.AddField(
            model_name='vlan',
            name='subnet_ip_v6',
            field=models.GenericIPAddressField(blank=True, default=None, null=True, verbose_name='子网IP(IPv6)'),
        ),
    ]
