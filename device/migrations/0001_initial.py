# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('compute', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='DBGPU',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('address', models.CharField(help_text='format:<domain>:<bus>:<slot>:<function>, example: 0000:84:00:0', max_length=100)),
                ('vm', models.CharField(null=True, max_length=200, blank=True)),
                ('attach_time', models.DateTimeField(null=True, blank=True)),
                ('enable', models.BooleanField(default=True)),
                ('remarks', models.TextField(null=True, blank=True)),
                ('host', models.ForeignKey(to='compute.Host')),
            ],
            options={
                'verbose_name_plural': '1_GPU',
                'verbose_name': 'GPU',
            },
        ),
    ]
