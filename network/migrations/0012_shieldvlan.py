# Generated by Django 3.2.13 on 2023-09-18 09:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('network', '0011_macip_ipv6'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShieldVlan',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('user_name', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_vlan_shield', to=settings.AUTH_USER_MODEL, verbose_name='用户')),
                ('vlan_id', models.ManyToManyField(blank=True, related_name='vlan_shield', to='network.Vlan', verbose_name='vlan')),
            ],
            options={
                'verbose_name': '对用户屏蔽vlan',
                'verbose_name_plural': '12_对用户屏蔽vlan',
                'ordering': ('id',),
            },
        ),
    ]
