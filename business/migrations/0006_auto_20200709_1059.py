# Generated by Django 3.0.5 on 2020-07-09 05:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0005_auto_20200708_0801'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deliveryboyjob',
            name='image',
            field=models.ImageField(upload_to='deliveryboy_images'),
        ),
        migrations.AlterField(
            model_name='shoponline',
            name='shop_image',
            field=models.ImageField(upload_to='shop_images'),
        ),
    ]
