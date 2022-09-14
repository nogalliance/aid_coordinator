# Generated by Django 4.0.3 on 2022-04-21 16:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("supply_demand", "0025_offer_created_at_offer_updated_at_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="offeritem",
            name="claimed_by",
        ),
        migrations.AlterField(
            model_name="offeritem",
            name="notes",
            field=models.CharField(
                blank=True,
                help_text="Any extra information that can help a requester decide if they can use this",
                max_length=250,
                verbose_name="notes",
            ),
        ),
    ]
