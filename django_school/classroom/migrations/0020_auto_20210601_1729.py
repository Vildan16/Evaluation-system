# Generated by Django 3.0.4 on 2021-06-01 17:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('classroom', '0019_teacher'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='first_name',
            field=models.CharField(blank=True, max_length=30, verbose_name='first name'),
        ),
    ]
