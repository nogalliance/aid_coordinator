# Generated by Django 4.0.3 on 2022-04-20 21:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        (
            "supply_demand",
            "0024_alter_offeritem_options_alter_requestitem_options_and_more",
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="Shipment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=100, unique=True, verbose_name="name"),
                ),
                ("when", models.DateField(blank=True, null=True, verbose_name="when")),
                (
                    "is_delivered",
                    models.BooleanField(default=False, verbose_name="is delivered"),
                ),
            ],
            options={
                "verbose_name": "shipment",
                "verbose_name_plural": "shipments",
            },
        ),
        migrations.CreateModel(
            name="Claim",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "amount",
                    models.PositiveIntegerField(
                        default=1,
                        help_text="The amount of items claimed",
                        verbose_name="amount",
                    ),
                ),
                (
                    "offered_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="supply_demand.offeritem",
                        verbose_name="offered item",
                    ),
                ),
                (
                    "requested_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="supply_demand.requestitem",
                        verbose_name="requested item",
                    ),
                ),
                (
                    "shipment",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="logistics.shipment",
                        verbose_name="shipment",
                    ),
                ),
            ],
            options={
                "verbose_name": "claim",
                "verbose_name_plural": "claim",
            },
        ),
    ]
