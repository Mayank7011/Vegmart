# Generated by Django 3.0.5 on 2020-07-06 17:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='shoponline',
            name='is_accepted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='shoponline',
            name='is_verified',
            field=models.BooleanField(default=False),
        ),
    ]
