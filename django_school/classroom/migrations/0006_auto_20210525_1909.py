# Generated by Django 3.0.4 on 2021-05-25 19:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('classroom', '0005_auto_20210525_2117'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='type',
            field=models.TextField(default='1', verbose_name='Type'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='user',
            name='first_name',
            field=models.CharField(blank=True, max_length=30, verbose_name='first name'),
        ),
    ]
