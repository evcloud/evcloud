# Generated by Django 3.2.13 on 2022-09-19 08:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ceph', '0003_auto_20200211_0931'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cephcluster',
            name='has_auth',
            field=models.BooleanField(default=True, help_text='未选中时，不使用uuid字段，uuid设置为空', verbose_name='需要认证'),
        ),
        migrations.AlterField(
            model_name='cephpool',
            name='enable',
            field=models.BooleanField(default=True, verbose_name='启用存储POOL'),
        ),
        migrations.AlterField(
            model_name='cephpool',
            name='has_data_pool',
            field=models.BooleanField(default=False, verbose_name='具备独立存储POOL'),
        ),
    ]
