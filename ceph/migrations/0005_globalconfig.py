# Generated by Django 3.2.13 on 2023-05-10 08:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ceph', '0004_auto_20220919_1608'),
    ]

    operations = [
        migrations.CreateModel(
            name='GlobalConfig',
            fields=[
                ('id', models.AutoField(default=1, primary_key=True, serialize=False)),
                ('sitename', models.CharField(default='EVcloud', max_length=50, verbose_name='站点名称')),
                ('poweredby', models.CharField(default='https://gitee.com/cstcloud-cnic/evcloud', max_length=255, verbose_name='技术支持')),
                ('novnchttp', models.CharField(default='http', help_text='配置novnchttp协议 http/https', max_length=10, verbose_name='novnc http协议配置')),
            ],
            options={
                'verbose_name': '站点配置',
                'verbose_name_plural': '站点配置',
                'db_table': 'site_global_config',
                'ordering': ['-id'],
            },
        ),
    ]
