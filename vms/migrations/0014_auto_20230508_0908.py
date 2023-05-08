# Generated by Django 3.2.13 on 2023-05-08 01:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('image', '0009_auto_20230222_1228'),
        ('ceph', '0004_auto_20220919_1608'),
        ('vms', '0013_auto_20220713_1929'),
    ]

    operations = [
        migrations.AddField(
            model_name='vm',
            name='architecture',
            field=models.SmallIntegerField(choices=[(1, 'x86-64'), (2, 'i386'), (3, 'arm-64'), (4, 'unknown')], default=1, verbose_name='系统架构'),
        ),
        migrations.AddField(
            model_name='vm',
            name='boot_mode',
            field=models.SmallIntegerField(choices=[(1, 'UEFI'), (2, 'BIOS')], default=2, verbose_name='系统启动方式'),
        ),
        migrations.AddField(
            model_name='vm',
            name='ceph_pool',
            field=models.ForeignKey(db_constraint=False, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='ceph.cephpool', verbose_name='CEPH存储后端'),
        ),
        migrations.AddField(
            model_name='vm',
            name='default_password',
            field=models.CharField(default='cnic.cn', max_length=32, verbose_name='系统默认登录密码'),
        ),
        migrations.AddField(
            model_name='vm',
            name='default_user',
            field=models.CharField(default='root', max_length=32, verbose_name='系统默认登录用户名'),
        ),
        migrations.AddField(
            model_name='vm',
            name='image_name',
            field=models.CharField(default='', max_length=100, verbose_name='镜像名称'),
        ),
        migrations.AddField(
            model_name='vm',
            name='image_parent',
            field=models.CharField(default='', help_text='虚拟机系统盘镜像的父镜像', max_length=255, verbose_name='父镜像RBD名'),
        ),
        migrations.AddField(
            model_name='vm',
            name='image_size',
            field=models.IntegerField(default=0, help_text='image size不是整Gb大小，要向上取整，如1.1GB向上取整为2Gb', verbose_name='镜像大小（Gb）'),
        ),
        migrations.AddField(
            model_name='vm',
            name='image_snap',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='镜像快照'),
        ),
        migrations.AddField(
            model_name='vm',
            name='nvme_support',
            field=models.BooleanField(default=False, verbose_name='支持NVME设备'),
        ),
        migrations.AddField(
            model_name='vm',
            name='release',
            field=models.SmallIntegerField(choices=[(1, 'Windows Desktop'), (2, 'Windows Server'), (3, 'Ubuntu'), (4, 'Fedora'), (5, 'Centos'), (6, 'Unknown')], default=5, verbose_name='系统发行版本'),
        ),
        migrations.AddField(
            model_name='vm',
            name='sys_type',
            field=models.SmallIntegerField(choices=[(1, 'Windows'), (2, 'Linux'), (3, 'Unix'), (4, 'MacOS'), (5, 'Android'), (6, '其他')], default=6, verbose_name='系统类型'),
        ),
        migrations.AddField(
            model_name='vm',
            name='version',
            field=models.CharField(default='', max_length=100, verbose_name='系统发行编号'),
        ),
        migrations.AddField(
            model_name='vm',
            name='image_desc',
            field=models.TextField(blank=True, default='', verbose_name='系统镜像描述'),
        ),
        migrations.AddField(
            model_name='vm',
            name='image_xml_tpl',
            field=models.TextField(default='', verbose_name='XML模板'),
        ),
    ]
