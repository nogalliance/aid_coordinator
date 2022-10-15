# Generated by Django 4.0.7 on 2022-09-28 09:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0025_auto_20220917_1635'),
    ]

    operations = [
        migrations.AddField(
            model_name='shipmentitem',
            name='last_location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='last_location', to='logistics.location', verbose_name='last location'),
        ),
    ]