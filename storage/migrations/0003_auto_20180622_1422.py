# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-06-22 14:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0002_cephhost_backend'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cephpool',
            options={'verbose_name': '存储卷', 'verbose_name_plural': '2_存储卷'},
        ),
        migrations.AlterField(
            model_name='cephhost',
            name='backend',
            field=models.CharField(choices=[('ceph', 'CEPH'), ('gfs', 'GFS'), ('local', 'LOCAL')], default='ceph', max_length=50),
        ),
    ]
