# Generated by Django 4.0.3 on 2022-11-27 15:10

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0039_rename_claim_shipmentitem_claim_tmp_and_more'),
        ('supply_demand', '0033_claim_notes_claim_updated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='claim',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='created at'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='claim',
            name='shipment_item',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='logistics.shipmentitem', verbose_name='shipment'),
        ),
    ]
