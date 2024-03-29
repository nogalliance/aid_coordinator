# Generated by Django 4.0.3 on 2022-04-02 23:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "supply_demand",
            "0018_alter_change_managers_offer_unused_item_handling_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="offer",
            name="unused_item_handling",
            field=models.PositiveIntegerField(
                choices=[
                    (0, "No preference"),
                    (10, "Return them to donor"),
                    (20, "Destroy them"),
                    (50, "Sell them and use funds for Ukraine"),
                    (100, "Sell them and use funds for Global NOG Alliance"),
                ],
                default=0,
                help_text="If we can't find a Ukrainian organisation that can use these items in a reasonable time, what should we do with them?",
                verbose_name="unused item handling",
            ),
        ),
    ]
