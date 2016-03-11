# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('compute', '__first__'),
        ('storage', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DBCephQuota',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('total', models.IntegerField(help_text='单位MB', verbose_name='集群总容量')),
                ('volume', models.IntegerField(help_text='单位MB', verbose_name='云硬盘容量')),
                ('group', models.OneToOneField(null=True, verbose_name='集群', blank=True, help_text='此字段为空时表示全局默认设置', to='compute.Group')),
            ],
            options={
                'verbose_name': 'Ceph云硬盘配额',
                'verbose_name_plural': '2_Ceph云硬盘配额',
            },
        ),
        migrations.CreateModel(
            name='DBCephVolume',
            fields=[
                ('uuid', models.CharField(primary_key=True, max_length=200, serialize=False)),
                ('creator', models.CharField(null=True, blank=True, max_length=200)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('size', models.IntegerField()),
                ('remarks', models.TextField(null=True, blank=True)),
                ('vm', models.CharField(null=True, blank=True, max_length=200)),
                ('attach_time', models.DateTimeField(null=True, blank=True)),
                ('dev', models.CharField(null=True, blank=True, max_length=100)),
                ('enable', models.BooleanField(default=True)),
                ('cephpool', models.ForeignKey(to='storage.CephPool')),
                ('group', models.ForeignKey(null=True, blank=True, to='compute.Group')),
                ('user', models.ForeignKey(null=True, blank=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Ceph云硬盘',
                'verbose_name_plural': '1_Ceph云硬盘',
            },
        ),
    ]
