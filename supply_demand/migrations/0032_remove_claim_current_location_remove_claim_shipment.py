# Generated by Django 4.0.7 on 2022-09-17 16:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('supply_demand', '0031_alter_claim_table'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='claim',
            name='current_location',
        ),
        migrations.RemoveField(
            model_name='claim',
            name='shipment',
        ),
    ]