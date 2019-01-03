# Generated by Django 2.0.2 on 2018-11-24 18:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0004_course_tag'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='url',
            field=models.CharField(default='', max_length=200, verbose_name='访问地址'),
        ),
        migrations.AlterField(
            model_name='course',
            name='category',
            field=models.CharField(default='后端开发', max_length=20, verbose_name='课程类别'),
        ),
        migrations.AlterField(
            model_name='course',
            name='tag',
            field=models.CharField(default='Python', max_length=10, verbose_name='课程标签'),
        ),
    ]