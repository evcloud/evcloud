# Generated by Django 3.2.5 on 2022-04-24 03:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('image', '0005_image_size'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='image',
            name='type',
        ),
        migrations.DeleteModel(
            name='ImageType',
        ),
    ]