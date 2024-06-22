# Generated by Django 5.0.6 on 2024-06-22 15:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network_automator_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='host',
            name='ipv4_address',
            field=models.GenericIPAddressField(default='0.0.0.0'),
        ),
        migrations.AddField(
            model_name='host',
            name='model',
            field=models.CharField(default='Model Unknown', max_length=32),
        ),
        migrations.AddField(
            model_name='host',
            name='vendor',
            field=models.CharField(max_length=32, null=True),
        ),
    ]
