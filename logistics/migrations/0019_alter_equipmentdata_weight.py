# Generated by Django 4.0.3 on 2022-07-04 17:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("logistics", "0018_equipmentdata_depth_equipmentdata_height_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="equipmentdata",
            name="weight",
            field=models.FloatField(blank=True, help_text="in kg", null=True, verbose_name="weight"),
        ),
    ]