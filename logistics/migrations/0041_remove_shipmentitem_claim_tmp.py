# Generated by Django 4.0.3 on 2022-11-27 15:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0040_auto_20221127_1510'),
        ('supply_demand', '0035_auto_20221127_1511')
    ]

    operations = [
        migrations.RemoveField(
            model_name='shipmentitem',
            name='claim_tmp',
        ),
    ]