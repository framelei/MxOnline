# Generated by Django 2.0.2 on 2018-11-28 18:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20181110_1709'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailverifyrecord',
            name='send_type',
            field=models.CharField(choices=[('register', '注册'), ('forget', '找回密码'), ('update_email', '更改邮箱')], max_length=20, verbose_name='发送类型'),
        ),
    ]