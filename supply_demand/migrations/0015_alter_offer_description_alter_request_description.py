# Generated by Django 4.0.3 on 2022-03-21 22:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("supply_demand", "0014_offer_delivery_method_offer_location"),
    ]

    operations = [
        migrations.AlterField(
            model_name="offer",
            name="description",
            field=models.CharField(
                blank=True,
                help_text="Give a short description of what this offer is",
                max_length=100,
                verbose_name="description",
            ),
        ),
        migrations.AlterField(
            model_name="request",
            name="description",
            field=models.TextField(
                blank=True,
                help_text="Provide more detail on this request, this is your elevator pitch!",
                verbose_name="description",
            ),
        ),
    ]
