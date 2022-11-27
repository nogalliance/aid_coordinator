# Generated by Django 4.0.3 on 2022-11-27 15:10

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('supply_demand', '0033_claim_notes_claim_updated_at'),
        ('logistics', '0038_alter_item_options'),
    ]

    operations = [
        migrations.RenameField(
            model_name='shipmentitem',
            old_name='claim',
            new_name='claim_tmp',
        ),
        migrations.AddField(
            model_name='shipmentitem',
            name='offered_item',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.RESTRICT, to='supply_demand.offeritem', verbose_name='offered_item'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='shipmentitem',
            name='amount',
            field=models.PositiveIntegerField(default=1, help_text='The amount of danated items', validators=[django.core.validators.MinValueValidator(1)], verbose_name='amount'),
        ),
    ]