# Generated by Django 3.2.6 on 2022-06-18 13:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20220618_1313'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='confirmation_code',
        ),
    ]
