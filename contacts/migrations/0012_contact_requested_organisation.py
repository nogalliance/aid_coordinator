# Generated by Django 4.0.3 on 2022-07-04 10:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contacts", "0011_alter_contact_options_alter_organisation_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="contact",
            name="requested_organisation",
            field=models.CharField(blank=True, max_length=100, verbose_name="requested organisation"),
        ),
    ]
