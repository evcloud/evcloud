# Generated by Django 3.2.13 on 2023-02-03 02:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compute', '0008_auto_20230203_0831'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='enable',
            field=models.BooleanField(default=True, verbose_name='启用宿主机组'),
        ),
    ]
