# Generated by Django 3.1.7 on 2021-05-26 19:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('classroom', '0009_auto_20210526_1911'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='takenquiz',
            name='score1',
        ),
        migrations.RemoveField(
            model_name='takenquiz',
            name='score2',
        ),
        migrations.RemoveField(
            model_name='takenquiz',
            name='score3',
        ),
    ]