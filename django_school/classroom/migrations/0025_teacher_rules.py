# Generated by Django 3.1.7 on 2021-06-09 13:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('classroom', '0024_student_rules'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacher',
            name='rules',
            field=models.BooleanField(default=False),
        ),
    ]
