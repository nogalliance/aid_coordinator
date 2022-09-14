# Generated by Django 4.0.3 on 2022-07-04 10:05

from django.db import migrations, models
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ("logistics", "0010_claim_current_location"),
    ]

    operations = [
        migrations.AddField(
            model_name="location",
            name="email",
            field=models.EmailField(blank=True, max_length=254, verbose_name="email contact"),
        ),
        migrations.AddField(
            model_name="location",
            name="is_collection_point",
            field=models.BooleanField(default=False, verbose_name="is a collection point"),
        ),
        migrations.AddField(
            model_name="location",
            name="phone",
            field=phonenumber_field.modelfields.PhoneNumberField(
                blank=True, max_length=128, region=None, verbose_name="phone contact"
            ),
        ),
    ]
