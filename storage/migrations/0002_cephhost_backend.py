# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-09 21:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cephhost',
            name='backend',
            field=models.CharField(choices=[('ceph', 'CEPH'), ('gfs', 'GFS'), ('local', 'LOCAL')], default='local', max_length=50),
        ),
    ]
