# Generated by Django 4.0.3 on 2022-04-18 09:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contacts", "0010_alter_contact_managers"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="contact",
            options={
                "ordering": ("first_name", "last_name", "username"),
                "verbose_name": "contact",
                "verbose_name_plural": "contacts",
            },
        ),
        migrations.AlterField(
            model_name="organisation",
            name="type",
            field=models.PositiveIntegerField(
                choices=[
                    (0, "Other"),
                    (100, "Commercial (generic)"),
                    (101, "Internet Provider"),
                    (102, "Internet Exchange"),
                    (150, "Equipment vendor"),
                    (200, "Non-Profit (generic)"),
                    (201, "Association"),
                    (202, "Foundation"),
                    (400, "Educational (generic)"),
                    (401, "University"),
                    (900, "Government (generic)"),
                    (901, "Regulator"),
                ],
                default=0,
                verbose_name="type",
            ),
        ),
    ]
