# Generated by Django 2.0.2 on 2018-11-26 19:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0004_auto_20181122_2208'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacher',
            name='teacher_age',
            field=models.IntegerField(blank=True, default=26, null=True, verbose_name='年龄'),
        ),
    ]
