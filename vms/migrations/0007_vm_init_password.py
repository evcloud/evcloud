# Generated by Django 2.2.10 on 2020-06-08 05:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vms', '0006_migratelog'),
    ]

    operations = [
        migrations.AddField(
            model_name='vm',
            name='init_password',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='root初始密码'),
        ),
    ]
