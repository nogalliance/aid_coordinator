# Generated by Django 4.0.3 on 2022-12-29 20:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0046_remove_shipmentitem_when'),
    ]

    operations = [
        migrations.AddField(
            model_name='shipment',
            name='parent_shipment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='logistics.shipment', verbose_name='parent shipment'),
        ),
        migrations.AlterField(
            model_name='shipmentitem',
            name='shipment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='logistics.shipment', verbose_name='shipment'),
        ),
    ]